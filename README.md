# ECOMMERCE.PY

## About
Ecommerce.py is a program based on Python language to extract the product name from a marketplace like [PetLove](petlove.com.br). The main idea is make easier to pick up some name that has already setup for you to use anyway you want to.

### Basic Guide 
First of all, the functions are in Brazilian Portuguese. You can change the name of the functions, but you must pay attention and avoid to forget some of them. 

### Input and Output Files 

To make this code functiona, you need to create a **.txt** file and add the EAN codes that you want to search. 

```
# Input/Output Settings
DESKTOP_PATH = os.path.join(os.path.expanduser('~'), 'Desktop')
INPUT_FILE = os.path.join(DESKTOP_PATH, 'EAN.txt')
OUTPUT_CSV = os.path.join(DESKTOP_PATH, 'results.csv')
```
