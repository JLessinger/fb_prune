import sys

if __name__ == '__main__':
    html = open('sdk.html', 'r').read()
    new_html = html % sys.argv[1]
    with open(sys.argv[2], 'w') as html_file:
        html_file.write(new_html)
