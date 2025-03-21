years = 5
money = 0 
invest = 0 # per month
start = 2000

money = (start + invest*12*years) * 1.04**(12*years)

print(f'{int(money):_}')