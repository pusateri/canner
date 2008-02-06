# format reStructured Text to plain text
SRCS = canner.rst tagger-api.rst
TXTS = $(SRCS:.rst=.txt)

all: $(TXTS)

clean:
	-rm -f $(TXTS)

.SUFFIXES: .rst .txt

.rst.txt:
	pandoc -o $@ $<
