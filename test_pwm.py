import wiringpi2 as wiringpi

# To work in both Python 2 and 3
try:
    input = raw_input
except NameError:
    pass


def main():
    wiringpi.wiringPiSetupGpio()
    wiringpi.pinMode(18,2)  # enable PWM mode on pin 18
    while True:
        newval = input("Enter a new PWM value: ")
        if newval == '':
	    wiringpi.pwmWrite(18, 0)
            break
        newval = int(newval)
        wiringpi.pwmWrite(18, newval)


if __name__ == '__main__':
    main()
