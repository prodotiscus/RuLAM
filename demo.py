import rulam

if __name__ == "__main__":
    parser = rulam.parser.get_parser(["Заяц бежит", "Он серый"])
    parser.readings(show_thread_readings=True, filter=True)
    # d0: ['s0-r0', 's1-r0'] : ([z1,z2],[zajats(z1), MALE(z1), bezhat(z1), (z2 = z1), seryj(z2), MALE(z2)])