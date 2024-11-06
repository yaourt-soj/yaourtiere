from os import mkdir


def create_directory(directory):
    directory_split = directory.split('/')
    current_layer = []
    for layer in directory_split:
        current_layer.append(layer)
        try:
            mkdir('/'.join(current_layer))
        except:
            pass
