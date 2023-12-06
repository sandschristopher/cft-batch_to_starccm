import numpy as np
import re
import csv
import os
import subprocess
from math import degrees, radians

def build_template(cft_batch_file, template_file):

    master = {}

    with open(cft_batch_file, 'r') as infile:
        data = infile.readlines()
        for line_number, line in enumerate(data):
            if "<ExportComponents " in line:
                num_components = int(line.split("\"")[1])
                for _ in range(1, num_components + 1):
                    for component_line in data[line_number + 1:line_number + num_components + 1]:
                        component = re.search("Caption=\"(.+?)\"", component_line).group(1)
                        index = re.search("Index=\"(.+?)\"", component_line).group(1)
                        if component not in master:
                            master[component] = {}
                            master[component]['index'] = index

    secondary_flow_path_sections = []
    mean_line_sections = []
    mer_data_sections = []

    with open(cft_batch_file, 'r') as infile, open(template_file, 'w') as outfile:
        data = infile.readlines()
        for component in master.keys():
            for line_number1, line1 in enumerate(data):
                if "Name=\"" + component in line1 and "CFturboDesign" in line1:
                    for line_number2, line2 in enumerate(data[line_number1:]):
                        section_end = "</" + line1.split(" ")[0].strip()[1:]
                        if section_end in line2:
                            section = data[line_number1:line_number1 + line_number2]
                            for line_number3, line3 in enumerate(section):

                                if "TMer2ndaryFlowPath" in line3:
                                    for line_number4, line4 in enumerate(data[(line_number1 + line_number3):]):
                                        if "</TMer2ndaryFlowPath>" in line4:
                                            secondary_flow_path_section = data[(line_number1 + line_number3):(line_number1 + line_number3 + line_number4)]
                                            break

                                    secondary_flow_path_sections.append(secondary_flow_path_section)

                                    for line_number5, line5 in enumerate(secondary_flow_path_section):
                                        if "<Wire" in line5:
                                            try:
                                                wire_name = re.search("Name=\"(.+?)\"", line5).group(1)
                                            except AttributeError:
                                                next
                                        
                                            for line_number6, line6 in enumerate(data[(line_number1 + line_number3 + line_number5):]):
                                                if "</Wire>" in line6:
                                                    wire_section = data[(line_number1 + line_number3 + line_number5):(line_number1 + line_number3 + line_number5 + line_number6)]
                                                    break

                                            for line_number7, line7 in enumerate(wire_section):
                                                
                                                if "<Connectors " in line7:
                                
                                                    for line_number8, line8 in enumerate(data[(line_number1 + line_number3 + line_number5 + line_number7):]):
                                                        
                                                        if "</Connectors>" in line8:
                                                            connectors_section = data[(line_number1 + line_number3 + line_number5 + line_number7):(line_number1 + line_number3 + line_number5 + line_number7 + line_number8)]
                                                            break

                                                    for line_number9, line9 in enumerate(connectors_section):
                                                        
                                                        if "<ConnectorPoint " in line9:
                                                            try:
                                                                point_index = re.search("Index=\"(.+?)\"", line9).group(1)
                                                            except AttributeError:
                                                                next
                                                            
                                                            for line_number10, line10 in enumerate(data[(line_number1 + line_number3 + line_number5 + line_number7 + line_number9):]):
                                                                
                                                                if "</ConnectorPoint>" in line10:
                                                                    point_section = data[(line_number1 + line_number3 + line_number5 + line_number7 + line_number9):(line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number10)]
                                                                    break

                                                            for line_number11, line11 in enumerate(point_section):
                                                                if "Caption=" in line11:
                                                                    variable = line11.split(" ")[0].strip()[1:]
                                                                    master[component][variable + wire_name + variable + point_index] = {}
                                                                    if "</" + variable + ">" in line11:
                                                                        try:
                                                                            var_type = re.search("Type=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + variable + point_index]['var_type'] = var_type
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            count = re.search("Count=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + variable + point_index]['count'] = count
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            caption = re.search("Caption=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + variable + point_index]['caption'] = caption
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            desc = re.search("Desc=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + variable + point_index]['desc'] = desc
                                                                        except AttributeError:
                                                                            next
                                                                        
                                                                        try:
                                                                            unit = re.search("Unit=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + variable + point_index]['unit'] = unit
                                                                        except AttributeError:
                                                                            next

                                                                        value = ">" + re.search(">(.*)</", line11).group(1) + "<"
                                                                        marker = ">{" + component + "_" + wire_name + "_" + variable + "_" + point_index + "_" + caption.replace(" ", '-') + "}<"
                                                                        data[line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number11] = data[line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number11].replace(value, marker)
                                                                    
                                                                        master[component][variable + wire_name + variable + point_index]['value'] = value
                                                                        master[component][variable + wire_name + variable + point_index]['marker'] = marker

                                                elif "<Curve " in line7:
                                                    try:
                                                        curve_index = re.search("Index=\"(.+?)\"", line7).group(1)
                                                    except AttributeError:
                                                        next
                                                    
                                                    for line_number8, line8 in enumerate(data[(line_number1 + line_number3 + line_number5 + line_number7):]):
                                                        if "</Curve>" in line8:
                                                            curve_section = data[(line_number1 + line_number3 + line_number5 + line_number7):(line_number1 + line_number3 + line_number5 + line_number7 + line_number8)]
                                                            break

                                                    for line_number9, line9 in enumerate(curve_section):
                                                        if "<ControlPoint" in line9:
                                                            try:
                                                                point_index = re.search("Index=\"(.+?)\"", line9).group(1)
                                                            except AttributeError:
                                                                next

                                                            for line_number10, line10 in enumerate(data[(line_number1 + line_number3 + line_number5 + line_number7 + line_number9):]):
                                                                if "</ControlPoint>" in line10:
                                                                    point_section = data[(line_number1 + line_number3 + line_number5 + line_number7 + line_number9):(line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number10)]
                                                                    break

                                                            for line_number11, line11 in enumerate(point_section):
                                                                if "Caption=" in line11:
                                                                    variable = line11.split(" ")[0].strip()[1:]
                                                                    master[component][variable + wire_name + "curve" + curve_index + variable + point_index] = {}
                                                                    if "</" + variable + ">" in line11:
                                                                        try:
                                                                            var_type = re.search("Type=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['var_type'] = var_type
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            count = re.search("Count=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['count'] = count
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            caption = re.search("Caption=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['caption'] = caption
                                                                        except AttributeError:
                                                                            next

                                                                        try:
                                                                            desc = re.search("Desc=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['desc'] = desc
                                                                        except AttributeError:
                                                                            next
                                                                        
                                                                        try:
                                                                            unit = re.search("Unit=\"(.+?)\"", line11).group(1)
                                                                            master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['unit'] = unit
                                                                        except AttributeError:
                                                                            next

                                                                        value = ">" + re.search(">(.*)</", line11).group(1) + "<"
                                                                        marker = ">{" + component + "_" + wire_name + "_curve" + curve_index + "_" + variable + "_" + point_index + "_" + caption.replace(" ", '-') + "}<"
                                                                        data[line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number11] = data[line_number1 + line_number3 + line_number5 + line_number7 + line_number9 + line_number11].replace(value, marker)
                                                                    
                                                                        master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['value'] = value
                                                                        master[component][variable + wire_name + "curve" + curve_index + variable + point_index]['marker'] = marker

                                if "<TMeanLine" in line3 and "Index=" in line3:

                                    try:
                                        index = re.search("Index=\"(.+?)\"", line3).group(1)
                                    except AttributeError:
                                        next

                                    for line_number4, line4 in enumerate(data[(line_number1 + line_number3):]):
                                        if "</TMeanLine>" in line4:
                                            mean_line_section = data[(line_number1 + line_number3):(line_number1 + line_number3 + line_number4)]
                                            break

                                    mean_line_sections.append(mean_line_section)

                                    for line_number5, line5 in enumerate(mean_line_section):
                                        if "Caption=" in line5 and "Array" in line5:

                                            markers = []
                                            values = []

                                            variable = line5.split(" ")[0].strip()[1:]
                                            master[component][variable] = {}

                                            try:
                                                var_type = re.search("Type=\"(.+?)\"", line5).group(1)
                                                master[component][variable]['var_type'] = var_type
                                            except AttributeError:
                                                next

                                            try:
                                                count = re.search("Count=\"(.+?)\"", line5).group(1)
                                                master[component][variable]['count'] = count
                                            except AttributeError:
                                                next

                                            try:
                                                caption = re.search("Caption=\"(.+?)\"", line5).group(1)
                                                master[component][variable]['caption'] = caption
                                            except AttributeError:
                                                next

                                            try:
                                                desc = re.search("Desc=\"(.+?)\"", line5).group(1)
                                                master[component][variable]['desc'] = desc
                                            except AttributeError:
                                                next
                                            
                                            try:
                                                unit = re.search("Unit=\"(.+?)\"", line5).group(1)
                                                master[component][variable]['unit'] = unit
                                            except AttributeError:
                                                next

                                            for line_number6, line6 in enumerate(mean_line_section):
                                                if "</" + variable + ">" in line6:
                                                    array_section = mean_line_section[line_number5:line_number6]
                                                    break

                                            for index in range(int(count)):
                                                for line_number7, line7 in enumerate(array_section):
                                                    if "Index=\"" + str(index) + "\"" in line7:
                                                        if "Type=\"" + "Vector" in line7:
                                                            for vector_index in range(1, 3):
                                                                vector_variable = data[line_number1 + line_number3 + line_number5 + line_number7 + vector_index].split(" ")[0].strip()[1:]
                                                                value = ">" + re.search(">(.*)</", data[line_number1 + line_number3 + line_number5 + line_number7 + vector_index]).group(1) + "<"
                                                                marker = ">{" + component + "_" + variable + "_" + vector_variable + "_" + str(index) + "}<"
                                                                data[line_number1 + line_number3 + line_number5 + line_number7 + vector_index] = data[line_number1 + line_number3 + line_number5 + line_number7 + vector_index].replace(value, marker)
                                                                values.append(value)
                                                                markers.append(marker)

                                            master[component][variable]['value'] = values
                                            master[component][variable]['marker'] = markers

                                            if "</" + variable + ">" in line5:

                                                try:
                                                    var_type = re.search("Type=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['var_type'] = var_type
                                                except AttributeError:
                                                    next

                                                try:
                                                    count = re.search("Count=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['count'] = count
                                                except AttributeError:
                                                    next

                                                try:
                                                    caption = re.search("Caption=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['caption'] = caption
                                                except AttributeError:
                                                    next

                                                try:
                                                    desc = re.search("Desc=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['desc'] = desc
                                                except AttributeError:
                                                    next
                                                
                                                try:
                                                    unit = re.search("Unit=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['unit'] = unit
                                                except AttributeError:
                                                    next

                                                value = ">" + re.search(">(.*)</", line5).group(1) + "<"
                                                marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "_" + index + "}<"
                                                data[line_number1 + line_number3 + line_number5] = data[line_number1 + line_number3 + line_number5].replace(value, marker)
                                            
                                                master[component][variable + index]['value'] = value
                                                master[component][variable + index]['marker'] = marker
                                        
                                        elif "Caption=" in line5:

                                            variable = line5.split(" ")[0].strip()[1:]
                                            master[component][variable + index] = {}
                                            if "</" + variable + ">" in line5:

                                                try:
                                                    var_type = re.search("Type=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['var_type'] = var_type
                                                except AttributeError:
                                                    next

                                                try:
                                                    count = re.search("Count=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['count'] = count
                                                except AttributeError:
                                                    next

                                                try:
                                                    caption = re.search("Caption=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['caption'] = caption
                                                except AttributeError:
                                                    next

                                                try:
                                                    desc = re.search("Desc=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['desc'] = desc
                                                except AttributeError:
                                                    next
                                                
                                                try:
                                                    unit = re.search("Unit=\"(.+?)\"", line5).group(1)
                                                    master[component][variable + index]['unit'] = unit
                                                except AttributeError:
                                                    next

                                                value = ">" + re.search(">(.*)</", line5).group(1) + "<"
                                                marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "_" + index + "}<"
                                                data[line_number1 + line_number3 + line_number5] = data[line_number1 + line_number3 + line_number5].replace(value, marker)
                                            
                                                master[component][variable + index]['value'] = value
                                                master[component][variable + index]['marker'] = marker

                                elif "MerEdge" in line3 and "Name" in line3:
                                    try:
                                        name = re.search("Name=\"(.+?)\"", line3).group(1)
                                    except AttributeError:
                                        next
                                    
                                    for line_number4, line4 in enumerate(data[(line_number1 + line_number3):]):
                                        if "</" + "MerEdge>" in line4:
                                            mer_edge_section = data[(line_number1 + line_number3 + 1):(line_number1 + line_number3 + line_number4)]
                                            break

                                    for line_number5, line5 in enumerate(mer_edge_section):
                                        
                                        variable = line5.split(" ")[0].strip()[1:]
                                        master[component][variable + name.replace(" ", "-")] = {}

                                        try:
                                            var_type = re.search("Type=\"(.+?)\"", line5).group(1)
                                            master[component][variable + name.replace(" ", "-")]['var_type'] = var_type
                                        except AttributeError:
                                            next

                                        try:
                                            count = re.search("Count=\"(.+?)\"", line5).group(1)
                                            master[component][variable + name.replace(" ", "-")]['count'] = count
                                        except AttributeError:
                                            next

                                        try:
                                            caption = re.search("Caption=\"(.+?)\"", line5).group(1)
                                            master[component][variable + name.replace(" ", "-")]['caption'] = caption
                                        except AttributeError:
                                            next

                                        try:
                                            desc = re.search("Desc=\"(.+?)\"", line5).group(1)
                                            master[component][variable + name.replace(" ", "-")]['desc'] = desc
                                        except AttributeError:
                                            next
                                        
                                        try:
                                            unit = re.search("Unit=\"(.+?)\"", line5).group(1)
                                            master[component][variable + name.replace(" ", "-")]['unit'] = unit
                                        except AttributeError:
                                            next

                                        try:    

                                            value = ">" + re.search(">(.*)</", line5).group(1) + "<"
                                            marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "_" + name.replace(" ", '-') + "}<"
                                            data[line_number1 + line_number3 + line_number5 + 1] = data[line_number1 + line_number3 + line_number5 + 1].replace(value, marker)
                                        except AttributeError:
                                            continue

                                        master[component][variable + name.replace(" ", "-")]['value'] = value
                                        master[component][variable + name.replace(" ", "-")]['marker'] = marker

                                elif "MerData" in line3 and "Name" in line3:

                                    try:
                                        name = re.search("Name=\"(.+?)\"", line3).group(1)
                                    except AttributeError:
                                        next

                                    for line_number4, line4 in enumerate(data[(line_number1 + line_number3):]):
                                        if "</" + "MerData>" in line4:
                                            mer_data_section = data[(line_number1 + line_number3 + 1):(line_number1 + line_number3 + line_number4)]
                                            break

                                    mer_data_sections.append(mer_data_section)

                                    for line_number5, line5 in enumerate(mer_data_section):
                                        if "Vector2" in line5:

                                            markers = []
                                            values = []

                                            variable = line5.split(" ")[0].strip()[1:]
                                            master[component][name.replace(" ", "-") + variable] = {}

                                            try:
                                                var_type = re.search("Type=\"(.+?)\"", line5).group(1)
                                                master[component][name.replace(" ", "-") + variable] ['var_type'] = var_type
                                            except AttributeError:
                                                next

                                            try:
                                                count = re.search("Count=\"(.+?)\"", line5).group(1)
                                                master[component][name.replace(" ", "-") + variable] ['count'] = count
                                            except AttributeError:
                                                next

                                            try:
                                                caption = re.search("Caption=\"(.+?)\"", line5).group(1)
                                                master[component][name.replace(" ", "-") + variable] ['caption'] = caption
                                            except AttributeError:
                                                next

                                            try:
                                                desc = re.search("Desc=\"(.+?)\"", line5).group(1)
                                                master[component][name.replace(" ", "-") + variable]['desc'] = desc
                                            except AttributeError:
                                                next
                                            
                                            try:
                                                unit = re.search("Unit=\"(.+?)\"", line5).group(1)
                                                master[component][name.replace(" ", "-") + variable]['unit'] = unit
                                            except AttributeError:
                                                next

                                            for vector_index in range(1, 3):
                                                vector_variable = data[line_number1 + line_number3 + line_number5 + vector_index + 1].split(" ")[0].strip()[1:]
                                                value = ">" + re.search(">(.*)</", data[line_number1 + line_number3 + line_number5 + vector_index + 1]).group(1) + "<"
                                                marker = ">{" + component + "_" + name.replace(" ", "-") + "_" + variable + "_" + caption.replace(" ", '-') + "_" + vector_variable + "}<"
                                                data[line_number1 + line_number3 + line_number5 + vector_index + 1] = data[line_number1 + line_number3 + line_number5 + vector_index + 1].replace(value, marker)
                                                values.append(value)
                                                markers.append(marker)

                                            master[component][name.replace(" ", "-") + variable]['value'] = values
                                            master[component][name.replace(" ", "-") + variable]['marker'] = markers   
                

                                elif "Caption=" in line3:
                                    if not any(line3 in string for string in mean_line_sections) and not any(line3 in string for string in secondary_flow_path_sections):
                                        variable = line3.split(" ")[0].strip()[1:]

                                        try:
                                            caption = re.search("Caption=\"(.+?)\"", line3).group(1)
                                        except AttributeError:
                                            next

                                        master[component][variable + caption.replace(" ", "-")] = {}

                                        if "</" + variable + ">" in line3:

                                            try:
                                                var_type = re.search("Type=\"(.+?)\"", line3).group(1)
                                                master[component][variable + caption.replace(" ", "-")]['var_type'] = var_type
                                            except AttributeError:
                                                next

                                            try:
                                                count = re.search("Count=\"(.+?)\"", line3).group(1)
                                                master[component][variable + caption.replace(" ", "-")]['count'] = count
                                            except AttributeError:
                                                next

                                            try:
                                                caption = re.search("Caption=\"(.+?)\"", line3).group(1)
                                                master[component][variable + caption.replace(" ", "-")]['caption'] = caption
                                            except AttributeError:
                                                next
                                            

                                            try:
                                                desc = re.search("Desc=\"(.+?)\"", line3).group(1)
                                                master[component][variable + caption.replace(" ", "-")]['desc'] = desc
                                            except AttributeError:
                                                next
                                            
                                            try:
                                                unit = re.search("Unit=\"(.+?)\"", line3).group(1)
                                                master[component][variable + caption.replace(" ", "-")]['unit'] = unit
                                            except AttributeError:
                                                next

                                            value = ">" + re.search(">(.*)</", line3).group(1) + "<"
                                            marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "}<"
                                            data[line_number1 + line_number3] = data[line_number1 + line_number3].replace(value, marker)
                                            master[component][variable + caption.replace(" ", "-")]['value'] = value
                                            master[component][variable + caption.replace(" ", "-")]['marker'] = marker   

                                        elif "Array1" in line3:

                                            markers = []
                                            values = []

                                            variable = line3.split(" ")[0].strip()[1:]
                                            master[component][variable] = {}

                                            try:
                                                var_type = re.search("Type=\"(.+?)\"", line3).group(1)
                                                master[component][variable]['var_type'] = var_type
                                            except AttributeError:
                                                next

                                            try:
                                                count = re.search("Count=\"(.+?)\"", line3).group(1)
                                                master[component][variable]['count'] = count
                                            except AttributeError:
                                                next

                                            try:
                                                caption = re.search("Caption=\"(.+?)\"", line3).group(1)
                                                master[component][variable]['caption'] = caption
                                            except AttributeError:
                                                next

                                            try:
                                                desc = re.search("Desc=\"(.+?)\"", line3).group(1)
                                                master[component][variable]['desc'] = desc
                                            except AttributeError:
                                                next
                                            
                                            try:
                                                unit = re.search("Unit=\"(.+?)\"", line3).group(1)
                                                master[component][variable]['unit'] = unit
                                            except AttributeError:
                                                next

                                            for line_number4, line4 in enumerate(data[(line_number1 + line_number3):]):
                                                if "</" + variable + ">" in line4:
                                                    array_section = data[(line_number1 + line_number3 + 1):(line_number1 + line_number3 + line_number4)]
                                                    break

                                            for index in range(int(count)):
                                                for line_number5, line5 in enumerate(array_section):
                                                    if "Index=\"" + str(index) + "\"" in line5:
                                                        if "Type=\"" + "Vector" in line5:
                                                            for vector_index in range(1, 3):
                                                                vector_variable = data[line_number1 + line_number3 + line_number5 + 1 + vector_index].split(" ")[0].strip()[1:]
                                                                value = ">" + re.search(">(.*)</", data[line_number1 + line_number3 + line_number5 + 1 + vector_index]).group(1) + "<"
                                                                marker = ">{" + component + "_" + variable + "_" + vector_variable + "_" + str(index) + "}<"
                                                                data[line_number1 + line_number3 + line_number5 + 1 + vector_index] = data[line_number1 + line_number3 + line_number5 + 1 + vector_index].replace(value, marker)
                                                                values.append(value)
                                                                markers.append(marker)

                                                    
                                                        elif "Type=\"" + "Float" + "\"" in line5:
                                                            value = ">" + re.search(">(.*)</", data[line_number1 + line_number3 + line_number5 + 1]).group(1) + "<"
                                                            marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "_" + str(index) + "}<"
                                                            data[line_number1 + line_number3 + line_number5 + 1] = data[line_number1 + line_number3 + line_number5 + 1].replace(value, marker)
                                                            values.append(value)
                                                            markers.append(marker)

                                            master[component][variable]['value'] = values
                                            master[component][variable]['marker'] = markers   

                                        elif "Vector2" in line3:
                                            if not any(line3 in string for string in mer_data_sections):

                                                markers = []
                                                values = []

                                                variable = line3.split(" ")[0].strip()[1:]
                                                master[component][variable] = {}

                                                try:
                                                    var_type = re.search("Type=\"(.+?)\"", line3).group(1)
                                                    master[component][variable]['var_type'] = var_type
                                                except AttributeError:
                                                    next

                                                try:
                                                    count = re.search("Count=\"(.+?)\"", line3).group(1)
                                                    master[component][variable]['count'] = count
                                                except AttributeError:
                                                    next

                                                try:
                                                    caption = re.search("Caption=\"(.+?)\"", line3).group(1)
                                                    master[component][variable]['caption'] = caption
                                                except AttributeError:
                                                    next

                                                try:
                                                    desc = re.search("Desc=\"(.+?)\"", line3).group(1)
                                                    master[component][variable]['desc'] = desc
                                                except AttributeError:
                                                    next
                                                
                                                try:
                                                    unit = re.search("Unit=\"(.+?)\"", line3).group(1)
                                                    master[component][variable]['unit'] = unit
                                                except AttributeError:
                                                    next

                                                for vector_index in range(1, 3):
                                                    vector_variable = data[line_number1 + line_number3 + vector_index].split(" ")[0].strip()[1:]
                                                    value = ">" + re.search(">(.*)</", data[line_number1 + line_number3 + vector_index]).group(1) + "<"
                                                    marker = ">{" + component + "_" + variable + "_" + caption.replace(" ", '-') + "_" + vector_variable + "}<"
                                                    data[line_number1 + line_number3 + vector_index] = data[line_number1 + line_number3 + vector_index].replace(value, marker)
                                                    values.append(value)
                                                    markers.append(marker)

                                                master[component][variable]['value'] = values
                                                master[component][variable]['marker'] = markers   
  
                            break

        outfile.writelines(data)

    simple = {}

    for component in master.keys():
        for variable in master[component].keys():
            if variable != "index":
                marker = master[component][variable].get('marker')
                unit = master[component][variable].get('unit')
                if type(marker) == str:
                    value = master[component][variable].get('value')
                    simple[marker] = (value, unit)
                if type(marker) == list:
                    for _ in range(len(marker)):
                        value = master[component][variable].get('value')[_]
                        simple[marker[_]] = (value, unit)

    return master, simple


def csv_to_np(simple, csv_file, project_name):

    header = ["Design#"] + [marker[2:-2] for marker in simple.keys()]

    first_row = [1] 
    units_row = ['-']
    
    for (original, unit) in simple.values():
        if unit == 'rad':
            first_row.append(str(round(degrees(float(original[1:-1])), 3)))
            units_row.append('deg')
        elif unit == None:
            first_row.append(str(original[1:-1]))
            units_row.append('-')
        else:
            first_row.append(str(original[1:-1]))
            units_row.append(unit)

    if not os.path.exists(project_name + "_starccm.csv"):
        with open(csv_file, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow((header))
            writer.writerow((units_row))
            writer.writerow((first_row))
            csvfile.close()

        pause = input("Fill the CSV file with the design parameters. Once complete, press the <ENTER> key to continue.")
    
    values_array = (np.genfromtxt(csv_file, dtype=str, delimiter=',', skip_header=2).T)[1:]

    return values_array

def build_designs(project_name, template_file, values_array, simple):

    designs = []

    for design_number, row in enumerate(values_array.T, start=1):

        design_file = project_name + "_Design" + str(design_number) + ".cft-batch"

        with open(template_file, 'r') as infile, open(design_file, 'w') as outfile:
            data = infile.readlines()

            for value_number, (marker, (original, unit)) in enumerate(simple.items()):
                for line_number, line in enumerate(data):        
                    if marker in line:
                        if unit == 'rad':
                            data[line_number] = line.replace(marker[1:-1], str(radians(float(row[value_number]))))
                        else:
                            data[line_number] = line.replace(marker[1:-1], row[value_number])
                            
                    if "<BaseFileName>" in line:
                        old_name = re.search("<BaseFileName>(.*)</BaseFileName>", line).group(1)
                        data[line_number] = line.replace(old_name, "Design" + str(design_number))

                    if "<OutputFile>" in line:
                        old_name = re.search("<OutputFile>(.*)</OutputFile>", line).group(1)
                        data[line_number] = line.replace(old_name, design_file.replace(".cft-batch", ".cft"))

            outfile.writelines(data)

        designs.append(design_file)

    return designs


def run_batch(batch_file, designs, cft_version):
    
    with open(batch_file, "a") as batch:
        for index, design in enumerate(designs):
            if index == 0:
                batch.truncate(0)

            batch.write("\"C:\Program Files\CFturbo " + cft_version + "\CFturbo.exe\" -batch \"" + design + "\"\n")

        batch.close()

    batch_path = os.path.abspath(batch_file)
    output_path = os.path.abspath("Output")
    if not os.path.exists(output_path):
        subprocess.call(batch_path)

    return 0


def build_starccm_csv(cft_file, csv_file, designs, simple, master, values_array):

    print(values_array)

    formatted_components = []

    for component in master.keys():
        formatted_components.append("".join(char for char in component if char.isalnum() or char in "_-"))

    formatted_markers = []
    
    for marker in simple.keys():
        formatted_marker = marker[2:-2]
        formatted_markers.append("".join(char for char in formatted_marker if char.isalnum() or char in "_-"))

    header = ["Design#", "Name"]

    with open(cft_file) as infile:
        data = infile.readlines()
        for _, line in enumerate(data):
            if "<IsActiveExtension" in line:
                isActiveExtension = re.search(">(.*)</", line).group(1)

        if isActiveExtension == "True":
            header = header + formatted_components + [formatted_components[-1] + "_" + "Extension"] + formatted_markers
        else:
            header = header + formatted_components + formatted_markers

    with open(csv_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow((header))

        for design_number in range(1, len(designs) + 1):
            row = [str(design_number), "Design " + str(design_number)]
            for component in master.keys():
                row.append("Design" + str(design_number) + "_" + "Co" + str(int(master[component].get('index')) + 1) + ".stp")
            if isActiveExtension == "True" and component == list(master)[-1]:
                row.append("Design" + str(design_number) + "_" + "Co" + str(int(master[component].get('index')) + 1) + "_Extension.stp")
            for variable_num, _ in enumerate(simple):
                print(values_array[variable_num, design_number - 1])
                row.append(values_array[variable_num, design_number - 1])
            writer.writerow((row))

    return 0

def main():

    project_name = "ProjectName"
    cft_version = "2023.1.5"

    master, simple = build_template(project_name + ".cft-batch", "template.cft-batch")
    values_array = csv_to_np(simple, project_name + "_design_variables.csv", project_name)
    designs = build_designs(project_name, "template.cft-batch", values_array, simple)
    run_batch(project_name + ".bat", designs, cft_version)
    build_starccm_csv(project_name + ".cft", project_name + "_starccm_design_manager.csv", designs, simple, master, values_array)

main()
