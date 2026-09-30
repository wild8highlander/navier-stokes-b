# Makefile — C++ verification track of the Smagorinsky-Kolmogorov program.
#
# Targets:
#   make          — build all binaries into build/
#   make run      — build and execute p1/p2/p3/p5/p5c/p5d (writes results/*.json)
#   make clean    — remove build/
#
# All outputs land in ../../results (run `make run` from code/cpp).

CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -march=native
BUILD    := build

.PHONY: all run clean

all: $(BUILD)/p1_lilly $(BUILD)/p2_closures $(BUILD)/p3_apriori_cpp $(BUILD)/p5_regularity $(BUILD)/p5c_stretch $(BUILD)/p5d_qr

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/p1_lilly: p1_lilly.cpp sk_core.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p1_lilly.cpp -o $@

$(BUILD)/p2_closures: p2_closures.cpp sk_core.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p2_closures.cpp -o $@

$(BUILD)/p3_apriori_cpp: p3_apriori_cpp.cpp sk_core.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p3_apriori_cpp.cpp -o $@

$(BUILD)/p5_regularity: p5_regularity.cpp sk_core.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p5_regularity.cpp -o $@

$(BUILD)/p5c_stretch: p5c_stretch.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p5c_stretch.cpp -o $@

$(BUILD)/p5d_qr: p5d_qr.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) p5d_qr.cpp -o $@

run: all
	@mkdir -p ../../results
	@(cd ../.. && ./code/cpp/build/p1_lilly)
	@(cd ../.. && ./code/cpp/build/p2_closures)
	@(cd ../.. && ./code/cpp/build/p3_apriori_cpp)
	@(cd ../.. && ./code/cpp/build/p5_regularity)
	@(cd ../.. && ./code/cpp/build/p5c_stretch)
	@(cd ../.. && ./code/cpp/build/p5d_qr)

clean:
	rm -rf $(BUILD)
