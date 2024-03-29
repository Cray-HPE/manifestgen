#
# MIT License
#
# (C) Copyright 2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
SHELL := /bin/bash

ifeq ($(NAME),)
NAME := $(shell basename $(shell pwd))
endif

ifeq ($(VERSION),)
VERSION := $(shell git describe --tags | tr -s '-' '~' | tr -d '^v')
endif

ifeq ($(PYTHON_VERSION),)
PYTHON_VERSION := $(shell awk -v replace="'" '/pythonVersion/{gsub(replace,"", $$NF); print $$NF; exit}' Jenkinsfile.github)
endif

SPEC_FILE := ${NAME}.spec
SOURCE_NAME := ${NAME}-${VERSION}

BUILD_DIR := $(PWD)/dist/rpmbuild
SOURCE_PATH := ${BUILD_DIR}/SOURCES/${SOURCE_NAME}.tar.bz2

all: rpm

rpm: print rpm_package_source rpm_build_source rpm_build

.PHONY: print
print:
	@printf "%-20s: %s\n" Name $(NAME)
	@printf "%-20s: %s\n" 'Python Version' $(PY_VERSION)
	@printf "%-20s: %s\n" Version $(VERSION)

prepare:
	@echo $(NAME)
	rm -rf dist
	mkdir -p $(BUILD_DIR)/SPECS $(BUILD_DIR)/SOURCES
	cp $(SPEC_FILE) $(BUILD_DIR)/SPECS/

rpm_package_source:
	tar --transform 'flags=r;s,^,/$(SOURCE_NAME)/,' --exclude .nox --exclude dist/rpmbuild -cvjf $(SOURCE_PATH) .

rpm_build_source:
	rpmbuild -ts $(SOURCE_PATH) --define "_topdir $(BUILD_DIR)"

rpm_build:
	rpmbuild -ba $(SPEC_FILE) --define "_topdir $(BUILD_DIR)"
