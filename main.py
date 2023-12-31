import escpos.printer

p = escpos.printer.Usb(0x28e9, 0x0289, out_ep= 0x03)
p.text("Hello World.\n")

