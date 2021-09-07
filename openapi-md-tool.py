#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import json


def exec(filename):
    # Opening JSON file
    # reader = open('openapi.json', 'r')
    reader = open(filename, 'r')
    data = json.load(reader)

    markdown_text = ''
    paths = data['paths']
    components = data['components']
    for path in paths:
        for method in paths[path]:
            data = paths[path][method]
            summary = get_dict_data(data, 'summary')
            operationId = get_dict_data(data, 'operationId')

            # 请求
            req_sheet = []
            req_demo_data = ''
            global req_demo
            req_demo = ''
            parameters = get_dict_data(data, 'parameters')
            if parameters != '':
                for parameter in parameters:
                    name = parameter['name']
                    get_param_detail('', name, parameter['schema'], components, req_sheet, 'parameters')
                req_demo = req_demo[:-1]
                req_demo_data = path + '?' + req_demo

            requestBody = get_dict_data(data, 'requestBody')
            if requestBody != '':
                content = requestBody['content']
                for item in content:
                    data_type = get_dict_data(content[item]['schema'], 'type')
                    if data_type == 'array':  # 数组结构
                        ref = content[item]['schema']['items']['$ref']
                    else:  # 结构体结构
                        ref = content[item]['schema']['allOf'][0]['$ref']
                    recursive_get_sheet_item('^', ref, components, req_sheet, 'requestBody')
                    req_demo = req_demo[:-1]
                    req_demo_data = """%s
{
%s              
}
"""
                    req_demo_data = req_demo_data % (path, req_demo)

            # 响应
            res_sheet = []
            responses = data['responses']
            res_200 = get_dict_data(responses, '200')
            if res_200 != '':
                content = res_200['content']
                for item in content:
                    ref = get_dict_data(content[item]['schema'], '$ref')
                    if ref != '':
                        recursive_get_sheet_item('^', ref, components, res_sheet, 'res_200')
            markdown_text = markdown_text + gen_md(summary, method, path, operationId,
                                                   gen_md_sheet('请求参数', req_sheet),
                                                   gen_md_sheet('响应参数', res_sheet),
                                                   req_demo_data)

    writer = open("接口文档.md", "w")
    writer.write(markdown_text)
    writer.close()

    # Closing file
    reader.close()


def get_dict_data(data, key):
    value = ''
    if key in data.keys():
        value = data[key]
    return value


def get_ref_type(ref, components):
    ref_list = ref.split('/')[2:]
    recursive = components
    for v in ref_list:
        recursive = recursive[v]
    return recursive['type']


def get_components_value(ref, components):
    ref_list = ref.split('/')[2:]
    recursive = components
    for v in ref_list:
        recursive = recursive[v]
    return recursive


def get_param_detail(symbol, name, item, components, sheet, req_type):    # parameter['schema']
    is_necessary = True
    if get_dict_data(item, 'allOf') != '':  # 使用gen client生成
        ref = item['allOf'][0]['$ref']
        recursive_get_sheet_item(symbol, ref, components, sheet, req_type)     # 递归遍历标签索引
        param_type = get_ref_type(ref, components)
        item_info = item['allOf'][1]
        description = get_dict_data(item_info, 'description')
        tag = get_dict_data(item_info, 'x-tag-name')
        if tag != '' and tag.find("omitempty") >= 0:
            is_necessary = False
    else:  # 自己定义的参数
        param_type = get_dict_data(item, 'type')
        if param_type == 'array':    # 数组递归遍历标签索引
            ref = item['items']['$ref']
            recursive_get_sheet_item(symbol, ref, components, sheet, req_type)
        if param_type != 'string':
            param_type = get_dict_data(item, 'format')
        description = get_dict_data(item, 'description')
        tag = get_dict_data(item, 'x-tag-name')
        if tag != '' and tag.find("omitempty") >= 0:
            is_necessary = False
    if is_necessary:
        necessary = '是'
    else:
        necessary = '否'

    sheet.append('| %s%s | %s | %s | %s |\n' % (symbol, name, param_type, necessary, description))

    global req_demo
    if req_type == 'parameters':
        req_demo = req_demo + name + '=&'
    elif req_type == 'requestBody':
        req_demo = req_demo + "    \"" + name + '\":,\n'
    return


def recursive_get_sheet_item(symbol, ref, components, sheet, req_type):
    components_value = get_components_value(ref, components)
    # print('components_value ', components_value)
    item_type = get_dict_data(components_value, 'type')
    if item_type == 'object':
        # 表格格式化，子结构前增加--，依次递归
        if symbol == '^':
            symbol = ''
        else:
            symbol = symbol + '--'
        properties = components_value['properties']
        for key in properties:
            name = key
            get_param_detail(symbol, name, properties[key], components, sheet, req_type)
    elif item_type == 'array':
        array_ref = get_dict_data(components_value['items'], '$ref')
        if array_ref != '':
            recursive_get_sheet_item(symbol, array_ref, components, sheet, req_type)
    return


def gen_md(tittle, method, path, function, req_sheet, res_sheet, req_param_demo):
    markdown_text = """
### %s
> %s %s
>
> %s

功能描述：
```

```
请求参数：
%s
响应参数：
%s
请求示例：
```
%s
```
响应示例：
```

```

"""
    return markdown_text % (tittle, method, path, function, req_sheet, res_sheet, req_param_demo)


def gen_md_sheet(name, lines_data):
    sheet_data = """
> 无 
"""
    if len(lines_data):
        sheet_data = """
| %s     | 参数类型 | 是否必填 | 参数说明                      |
| ------------ | -------- | -------- | ----------------------------- |   
"""
        sheet_data = sheet_data % name
        for line in lines_data:
            sheet_data += line

    return sheet_data


if __name__ == '__main__':
    length = len(sys.argv)
    msg = """功能：
    根据openapi.json生成markdown文档
格式:
    [openapi-md-tool 文件名]
    eg: openapi-md-tool openapi.json
"""
    print(msg)
    if length != 2:
        print('error: 输入参数格式不对')
        sys.exit()
    filename = sys.argv[1]
    exec(filename)
    print('done')
