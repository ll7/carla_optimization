#!/usr/bin/env python3

variable_name = 'y'

result = ''

number_of_variables = 10

for i in range(number_of_variables):
    result += variable_name + '_' + str(i) + ', '

print(result)