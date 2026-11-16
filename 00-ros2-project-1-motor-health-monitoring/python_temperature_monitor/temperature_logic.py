def check_temperature(temperature, threshold):
    if temperature > threshold:
        return 'HOT'
    return 'NORMAL'
