# NSB C++ Lab — build automation
CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -pthread
TARGET    = nsb_lab

all: $(TARGET)

$(TARGET): nsb_lab.cpp
	$(CXX) $(CXXFLAGS) nsb_lab.cpp -o $(TARGET)

run: $(TARGET)
	./$(TARGET) --quick --lang en

selftest: $(TARGET)
	./$(TARGET) --selftest

clean:
	rm -f $(TARGET)

.PHONY: all run selftest clean
