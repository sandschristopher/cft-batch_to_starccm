import shutil
from tracemalloc import start
import numpy as np
import re
import csv
import os
import subprocess
from math import radians

'''
Takes .txt file filled with parameter values and converts it into a numpy array (column vector is one geometry variation).
Dimensions should be in [m] and angles should be in [deg].

Inputs:
txt_file [string] = name of .txt file containing geometry variation parameters
delimeter [string] = delimiter used within .txt file
'''
def txt_to_np(txt_file, delimiter):

    array = []

    with open(txt_file) as txt:
        data = txt.readlines()
        for line in data:
            array.append(line.rstrip().split(delimiter))
    
    values_array = np.array(array, dtype=object).T

    return values_array


'''
Takes original .cft-batch file and creates a blank .cft-batch template for parameter manipulation.

Inputs:
cft_batch_file [string] = name of original .cft-batch file exported from CFturbo software
template_file [string] = name of output .cft-batch template 
'''
def make_template(cft_batch_file, template_file):

    components = []
    formatted_components = []

    with open(cft_batch_file, "r") as cft_batch:
        data = cft_batch.readlines()
        for line_number, line in enumerate(data):
            if "ExportComponents " in line:
                num_components = int(line.split("\"")[1])

                for index in range(1, num_components + 1):
                    component = data[line_number + index].split("\"")[3]
                    components.append(component)
                    formatted_components.append("".join(char for char in component if char.isalnum() or char in "_-"))
    
        cft_batch.close()

    variables = []

    with open(cft_batch_file, "r") as cft_batch:
        data = cft_batch.readlines()
        for line_number, line in enumerate(data):
            if "Type=" in line and "</" in line and "ExportInterface" not in line and bool(set(line.split("\"")) & set(components)) == False:
                value = re.search(">(.*)</", line).group(1)
                variable = re.search("</(.*)>", line).group(1)
                newline = line.replace(value, "{" + variable + "}")
                data[line_number] = newline
                variables.append(variable)

            if "ExportComponents " in line:
                for index in range(0, num_components):
                    newline = data[line_number + index + 1].replace(components[index], formatted_components[index])
                    data[line_number + index + 1] = newline
                break

        cft_batch.close()
    
    with open(template_file, "w") as template:
        template.writelines(data)
        template.close()

    units = []

    with open(cft_batch_file, "r") as cft_batch:
        data = cft_batch.readlines()
        for line_number, line in enumerate(data):
            if "Caption=" in line and "Desc=" in line:
                if "Array" in line:
                    unit = re.search("Unit=\"(.*)\"", line).group(1)

                    var = line.split(" ")[0].lstrip()[1:]
                    key = "</" + var + ">"
            
                    count = 0
                    while True:
                        if key in data[(line_number + 1) + count]:
                            break
                        count += 1

                    units += [unit] * count 

                elif "Vector" in line:
                    count = int(re.search("([\d])", line).group(1))
                    unit = re.search("Unit=\"(.*)\"", line).group(1)
                    units += [unit] * count 

                elif "Unit" not in line:
                    unit = "-"
                    units.append(unit)

                else:
                    unit = re.search("Unit=\"(.*)\"", line).group(1)
                    units.append(unit)
        
        cft_batch.close()
       
    return variables, units, components, formatted_components


'''
Assigns geometry variation parameters to new .cft-batch files.

Inputs:
template_file [string] = name of output .cft-batch template 
variables [list] = list of variable names used to find the associated parameter values (from make_template())
values_array [np.array] = np.array of geometry parameter values (from txt_to_np())
output_folder [string] = name of output file containing the resulting geometry variations
base_name [string] = base name of folder containing .stp files
'''
def make_variations(cft_batch_file, template_file, variables, units, components, values_array, output_folder, base_name):

    original_values = [[] for _ in range(len(units))]

    with open(cft_batch_file, "r") as cft_batch:
        data = cft_batch.readlines()
        count = 0
        for line_number, line in enumerate(data):
            if "Type=" in line and "</" in line and "ExportInterface" not in line and bool(set(line.split("\"")) & set(components)) == False:
                value = re.search(">(.*)</", line).group(1)
                original_values[count] = [value]
                count += 1

    original_values = np.array(original_values)

    variations = []

    entire_values_array = np.hstack((original_values, values_array))

    for i, column in enumerate(entire_values_array.T, start=1):

        new_file = base_name + str(i) + ".cft-batch"

        with open(template_file, "r") as template:
            data = template.readlines()

            for j, value in enumerate(column):

                if units[j] == "rad" and i != 0:
                    value = str(radians(float(value)))

                key = "{" + variables[j] + "}"
                 
                for line_number, line in enumerate(data):
                    if key in line:
                        data[line_number] = line.replace(key, value)
                        break

            for line_number, line in enumerate(data):
                if "<WorkingDir>" in line:
                    old_directory = re.search("<WorkingDir>(.*)</WorkingDir>", line).group(1)
                    new_directory = ".\\" + output_folder + "\\"
                    data[line_number] = line.replace(old_directory, new_directory)

                if "<BaseFileName>" in line:
                    old_name = re.search("<BaseFileName>(.*)</BaseFileName>", line).group(1)
                    data[line_number] = line.replace(old_name, base_name + str(i))

            with open(new_file, "w+") as new:
                new.writelines(data)
                new.close()

            template.close()

        variations.append(new_file)

    for index, value in enumerate(original_values):
        if units[index] == "rad":
            original_values[index] = str(round(float(value)*57.2958))

    values_array = np.hstack((original_values, values_array))

    return variations, values_array


'''
Places each variation into a .bat file the runs .bat file.

Inputs:
batch_file [string] = name of output .bat file
variations [list] = list of variation file names (from make_variations())
'''
def make_batch(batch_file, variations, output_folder):
    
    with open(batch_file, "a") as batch:
        for index, variation in enumerate(variations):
            if index == 0:
                batch.truncate(0)

            batch.write("\"C:\Program Files\CFturbo 2021.2.2\CFturbo.exe\" -batch \"" + variation + "\"\n")

        batch.close()

    batch_path = os.path.abspath(batch_file)
    output_path = os.path.abspath(output_folder)
    if not os.path.exists(output_path):
        subprocess.call(batch_path)

    return 0


'''
Builds the proper file structure for Star-CCM.

Inputs:
formatted_components [list] = list of formatted component names within the .cft-batch file (from make_template())
output_folder [string] = name of output file containing the resulting geometry variations
'''
def build_file_hierarchy(formatted_components, output_folder):

    output_path = os.path.abspath(output_folder)

    stp_files = []
    extension_files = []

    for file in os.listdir(output_path):
        if "Extension" in file:
            extension_files.append(file)
        elif ".stp" in file:
            stp_files.append(file)
            
    stp_files = sorted(stp_files, key=lambda file: re.search("Co(.*)", file).group(1))

    final_list = [[] for _ in range(len(formatted_components))]

    for Co in range(len(formatted_components)):
        for file in stp_files:
            if re.search("_Co(\d+).stp", file).group(1) == str(Co + 1):
                final_list[Co].append(file)

    if len(extension_files) != 0:
        formatted_components = formatted_components + [formatted_components[-1] + "_Extension"]

    if not os.path.exists(os.path.join(output_path, formatted_components[0])):
        for index, component in enumerate(final_list):

            new_path = os.path.join(output_path, formatted_components[index])

            if not os.path.exists(new_path):
                os.mkdir(new_path)

                for file in component:
                    old_path = os.path.join(output_path, file)
                    shutil.move(old_path, new_path)
            
        if len(extension_files) != 0:
            new_path = os.path.join(output_path, formatted_components[-1] + "_Extension")

            if not os.path.exists(new_path):
                os.mkdir(new_path)

                for index, file in enumerate(extension_files):
                    old_path = os.path.join(output_path, file)
                    shutil.move(old_path, new_path)

        for file in os.listdir(output_path):
            if ".py" in file[-3:]:
                os.remove(os.path.join(output_path, file))

        for i, file in enumerate(os.listdir(output_path)):
            file_path = os.path.join(output_path, file)
            for j, stp in enumerate(os.listdir(file_path), start=1):
                os.rename(os.path.join(file_path, stp), os.path.join(file_path, "Design" + str(j) + "_" + formatted_components[i] + ".stp"))

    return formatted_components


'''
Builds a .csv file that follows the tabular format within Star-CCM+'s .

Inputs:
csv_file [string] = name of output .csv file
components [list] = list of component names within the .cft-batch file (from make_template())
variations [list] = list of variation file names (from make_variations())
base_name [string] = .stp file name prefix / output folder name (e.g. design, variation, stage, etc.)
'''
def build_csv(csv_file, variations, variables, formatted_components, values_array, output_folder, base_name):

    header = ["Design#", "Name"]

    for folder in os.listdir(os.path.abspath(output_folder)):
        header.append(folder)

    for variable in variables:
        header.append(variable)

    with open(csv_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow((header))

        for variation in range(1, len(variations) + 1):
            row = [str(variation), "Design " + str(variation)]
            for column in header[2:(len(formatted_components) + 2)]:
                row.append(base_name + str(variation) + "_" + column + ".stp")
            for index in range(len(variables)):
                row.append(values_array[index, variation - 1])
            writer.writerow((row))

    return 0

def main():
    values_array = txt_to_np("panthalassa.txt", "\t")
    variables, units, components, formatted_components = make_template("panthalassa.cft-batch", "template.cft-batch")
    base_name = "Design"
    output_folder = "Output"
    variations, values_array = make_variations("panthalassa.cft-batch", "template.cft-batch", variables, units, components, values_array, output_folder, base_name)
    make_batch("panthalassa.bat", variations, output_folder)
    final_components = build_file_hierarchy(formatted_components, output_folder)
    build_csv("panthalassa.csv", variations, variables, final_components, values_array, output_folder, base_name)

main()