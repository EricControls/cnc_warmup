
# cnc warmup

This warmup scrip generates a warmup file for Heidenhain controller


# how to install


## macos

Step:

1.  clone this repository
2.  cd into the repository with 'cd cnc\_warmup'
3.  create a virtual environment
    
        python -m venv venv
4.  source file
    
        source venv/bin/activate
5.  install
    
        pip install -e ".[dev]"
6.  confirm installation
    
        cnc-warmup --help


## how to use

Example:

    cnc_warmup small 1 -o output/small_warmup.h

Run the help for more info:

    cnc-warmup --help

