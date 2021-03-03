#!/usr/bin/env python3

variable_name = 'x'

result = ''

bound = '(-2.0, 2.0)'

number_of_variables = 10

for i in range(number_of_variables):
    result += ('\''+ variable_name + '_' + str(i) + '\': ' + bound + ', \n')

print(result)