class Background:
    height = None
    width = None
    mean = None
    image = None
    
    def __init__(self):
        self.height = 0
        self.width = 0
        self.mean = 0
        self.image = None
        self.napari_layer = None
    