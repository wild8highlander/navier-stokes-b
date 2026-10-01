# Makefile для NSB LAB 96 (C++ edition)
# build: make          -> ./nsb_lab_cpp
# run:   make run      -> интерактивное меню
# clean: make clean
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall

all: nsb_lab_cpp

nsb_lab_cpp: nsb_lab.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

run: nsb_lab_cpp
	./nsb_lab_cpp

run-en: nsb_lab_cpp
	./nsb_lab_cpp --lang en

clean:
	rm -f nsb_lab_cpp

.PHONY: all run run-en clean
