from escpos import printer




# Setup the printer stuff
p = printer.Usb(0x28e9, 0x0289, out_ep= 0x03, profile = "ZJ-5870")
