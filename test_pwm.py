from fishbox import wiring

# To work in both Python 2 and 3
try:
    input = raw_input
except NameError:
    pass


_PIN = 18


def main():
    while True:
        newval = input("Enter a new PWM value: ")
        if newval == '':
            wiring.pwm(_PIN, 0)
            break
        newval = int(newval)
        wiring.pwm(_PIN, newval)


if __name__ == '__main__':
    main()
