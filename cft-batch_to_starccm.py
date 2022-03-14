import numpy as np
import re
import csv
import os
import subprocess
from math import degrees, radians

'''
Takes .txt file containing the parameter values and converts it into a numpy array.
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


def build_template(cft_batch_file, template_file):

    master = {}

    with open(cft_batch_file, 'r') as infile, open(template_file, 'w') as outfile:
        data = infile.readlines()
        for line_number1, line1 in enumerate(data):
            if "<ExportComponents " in line1:
                num_components = int(line1.split("\"")[1])
                for index in range(1, num_components + 1):
                    for line_number2, line2 in enumerate(data):
                        component = re.search("Caption=\"(.+?)\"", data[line_number1 + index]).group(1)
                        formatted_component = "".join(char for char in component if char.isalnum() or char in "_-")
                        if formatted_component not in master:
                            master[formatted_component] = {}
                        if "Name=\"" + component in line2:
                            book_end = line2.split(" ")[0].strip()[1:]
                            for line_number3, line3 in enumerate(data):
                                if "</" + book_end in line3:
                                    section = data[line_number2:line_number3]
                                    for line_number4, line4 in enumerate(section):
                                        if "Caption=" in line4:
                                            variable = line4.split(" ")[0].strip()[1:]
                                            master[formatted_component][variable] = {}

                                            try:
                                                var_type = re.search("Type=\"(.+?)\"", line4).group(1)
                                                master[formatted_component][variable]['var_type'] = var_type
                                            except AttributeError:
                                                next

                                            try:
                                                count = re.search("Count=\"(.+?)\"", line4).group(1)
                                                master[formatted_component][variable]['count'] = count
                                            except AttributeError:
                                                next

                                            try:
                                                caption = re.search("Caption=\"(.+?)\"", line4).group(1)
                                                master[formatted_component][variable]['caption'] = caption
                                            except AttributeError:
                                                next

                                            try:
                                                desc = re.search("Desc=\"(.+?)\"", line4).group(1)
                                                master[formatted_component][variable]['desc'] = desc
                                            except AttributeError:
                                                next
                                            
                                            try:
                                                unit = re.search("Unit=\"(.+?)\"", line4).group(1)
                                                master[formatted_component][variable]['unit'] = unit
                                            except AttributeError:
                                                next

                                            values = []
                                            markers = []

                                            if "<TMeanLine" in section[line_number4 - 1]:
                                                index = int(re.search("Index=\"(.+?)\"", section[line_number4 - 1]).group(1)) + 1
                                                value = float(re.search(">(.*)</", line4).group(1))
                                                marker = "{" + formatted_component + "_" + variable + "_MeanLine" + str(index) + "}"

                                                data[line_number2 + line_number4] = data[line_number2 + line_number4].replace(str(value), marker)
                                                master[formatted_component][variable]['value'] = value
                                                master[formatted_component][variable]['marker'] = marker

                                                    

                                            elif var_type == "Array1":
                                                for line_number5, line5 in enumerate(section):
                                                    if "</" + variable + ">" in line5:
                                                        for line_number6, line6 in enumerate(section[(line_number4 + 1):line_number5]):
                                                            try:
                                                                index = line_number6 + 1
                                                                value = float(re.search(">(.*)</", line6).group(1))
                                                                marker = "{" + formatted_component + "_" + variable + "_MeanLine" + str(index) + "}"
                                                                values.append(value)
                                                                markers.append(marker)
                                                            except AttributeError:
                                                                next

                                                            data[line_number2 + line_number4 + 1 + line_number6] = data[line_number2 + line_number4 + 1 + line_number6].replace(str(value), marker)
                                                        
                                                        master[formatted_component][variable]['value'] = values
                                                        master[formatted_component][variable]['marker'] = markers
                                            
                                            elif var_type == "Vector2":
                                                for line_number5, line5 in enumerate(section):
                                                    if "</" + variable + ">" in line5:
                                                        for line_number6, line6 in enumerate(section[(line_number4 + 1):line_number5]):
                                                            try:
                                                                coordinate = line6.split(" ")[0].strip()[1:]
                                                                value = float(re.search(">(.*)</", line6).group(1))
                                                                marker = "{" + formatted_component + "_" + variable + "_" + coordinate + "}"
                                                                values.append(value)
                                                                markers.append(marker)
                                                            except AttributeError:
                                                                next

                                                            data[line_number2 + line_number4 + 1 + line_number6] = data[line_number2 + line_number4 + 1 + line_number6].replace(str(value), marker)
                                                        
                                                        master[formatted_component][variable]['value'] = values
                                                        master[formatted_component][variable]['marker'] = markers

                                            else:
                                                try:
                                                    if var_type == "Integer":
                                                        value = int(re.search(">(.*)</", line4).group(1))
                                                    else: 
                                                        value = float(re.search(">(.*)</", line4).group(1))
                                                    
                                                    marker = "{" + formatted_component + "_" + variable + "}"
                                                except AttributeError:
                                                    next

                                                data[line_number2 + line_number4] = data[line_number2 + line_number4].replace(str(value), marker)
                                                
                                                master[formatted_component][variable]['value'] = value
                                                master[formatted_component][variable]['marker'] = marker

        for line_number7, line7 in enumerate(data):
            if "<WorkingDir>" in line7:
                old_directory = re.search("<WorkingDir>(.*)</WorkingDir>", line7).group(1)
                new_directory = ".\\" + "Output" + "\\"
                data[line_number7] = line7.replace(old_directory, new_directory)

        outfile.writelines(data)

    simple = {}

    for formatted_component in master.keys():
        for variable in master[formatted_component].keys():
            marker = master[formatted_component][variable].get('marker')
            unit = master[formatted_component][variable].get('unit')
            if type(marker) == str:
                value = master[formatted_component][variable].get('value')
                simple[marker] = (value, unit)
            if type(marker) == list:
                for index, item in enumerate(marker):
                    value = master[formatted_component][variable].get('value')[index]
                    simple[marker[index]] = (value, unit)

    return master, simple

def build_designs(template_file, values_array, simple):

    designs = []

    for design_number, row in enumerate(values_array.T, start=1):

        design_file = "Design" + str(design_number) + ".cft-batch"

        with open(template_file, 'r') as infile, open(design_file, 'w') as outfile:
            data = infile.readlines()

            for value_number, (marker, (original, unit)) in enumerate(simple.items()):
                for line_number, line in enumerate(data):
                    if design_number == 1:
                        if marker in line:
                            data[line_number] = line.replace(marker, str(original))
                    
                    else:
                        if marker in line:
                            if unit == 'rad':
                                data[line_number] = line.replace(marker, str(radians(float(row[value_number]))))
                            else:
                                data[line_number] = line.replace(marker, row[value_number])
                    
                    if "<BaseFileName>" in line:
                        old_name = re.search("<BaseFileName>(.*)</BaseFileName>", line).group(1)
                        data[line_number] = line.replace(old_name, "Design" + str(design_number))
                        break
        
            outfile.writelines(data)

        designs.append(design_file)

    return designs


def run_batch(batch_file, designs):
    
    with open(batch_file, "a") as batch:
        for index, design in enumerate(designs):
            if index == 0:
                batch.truncate(0)

            batch.write("\"C:\Program Files\CFturbo 2021.2.2\CFturbo.exe\" -batch \"" + design + "\"\n")

        batch.close()

    batch_path = os.path.abspath(batch_file)
    output_path = os.path.abspath("Output")
    if not os.path.exists(output_path):
        subprocess.call(batch_path)

    return 0


def build_csv(csv_file, designs, simple, master, values_array):

    header = ["Design#", "Name"]

    header = header + [formatted_component for formatted_component in master.keys()] + [marker[1:-1] for marker in simple.keys()]

    with open(csv_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow((header))

        for design_number in range(1, len(designs) + 1):
            row = [str(design_number), "Design " + str(design_number)]
            for component_number in range(1, len(master) + 1):
                row.append("Design" + str(design_number) + "_" + "Co" + str(component_number) + ".stp")
            for variable_num, variable in enumerate(simple):
                original, unit = simple.get(variable)
                if design_number == 1:
                    if unit == "rad":
                        row.append(round(degrees(original), 3))
                    else:
                        row.append(original)
                else:
                    row.append(values_array[variable_num, design_number - 1])
            writer.writerow((row))

    return 0

def main():
    values_array = txt_to_np("panthalassa.txt", "\t")
    master, simple = build_template("panthalassa.cft-batch", "template.cft-batch")
    designs = build_designs("template.cft-batch", values_array, simple)
    run_batch("panthalassa.bat", designs)
    build_csv("panthalassa.csv", designs, simple, master, values_array)

main()