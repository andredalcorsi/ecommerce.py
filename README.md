# WEBSCRAPING | ECOMMERCE.PY

## About
Ecommerce.py is a webscraper based on Python language to extract focuse to extrat product names from every marketplace whose let you search by the bar code on Search Bar. The main idea is make easier to pick up some name that has already setup for you to use anyway you want to.

### Basic Guide 
First of all, the functions are in Brazilian Portuguese. You can change the name of the functions, but you must pay attention and avoid to forget all of them. 

### Input and Output Files 

To make this code functional, you need to create a **.txt** file and add the EAN **(European Article File / International Article File)** that you want to search. The pattern path is settled up as below. You need to change the path according your system (Linux/MacOS/Windows): 

```
# Input/Output Settings
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'EAN.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'results.csv')

```

**NOTE**: The **.txt** file need to be in your Desktop, like the representation on this print screen :point_down: | As pattern, the **.csv** file will be created on the desktop folder, too. 

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/1e38c2a6-cd8d-4579-8edc-6491df19e31e" />

