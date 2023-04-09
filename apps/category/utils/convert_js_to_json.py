import json

def convert_js_to_json(file_path, output_path):
    with open(file_path, 'r') as file:
        content = file.read()
    # remove the "export const categories = " part
    content = content.split('=', 1)[1]
    # remove the last ";"
    content = content[:-1]
    # parse the json
    data = json.loads(content)
    # write json to file
    with open(output_path, 'w') as outfile:
        json.dump(data, outfile)
    print(f'Data written to {output_path}')

if __name__ == '__main__':
    file_path = './categories.js'
    output_path = './data.json'
    convert_js_to_json(file_path, output_path)