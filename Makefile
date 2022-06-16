SHELL := /bin/bash

NAME ?= ${GIT_REPO_NAME}
VERSION ?= $(shell git describe --tags | tr -s '-' _)

BUILD_METADATA ?= "1~development~$(shell git rev-parse --short HEAD)"
RPM_SPEC_FILE ?= ${NAME}.spec
RPM_SOURCE_NAME ?= ${NAME}-${VERSION}
RPM_BUILD_DIR ?= $(PWD)/dist/rpmbuild
RPM_SOURCE_PATH := ${RPM_BUILD_DIR}/SOURCES/${RPM_SOURCE_NAME}.tar.gz

all: build_prep built_test rpm build_post
rpm: rpm_package_source rpm_build_source rpm_build

prepare:
	rm -rf $(RPM_BUILD_DIR)
	mkdir -p $(RPM_BUILD_DIR)/SPECS $(RPM_BUILD_DIR)/SOURCES
	cp $(RPM_SPEC_FILE) $(RPM_BUILD_DIR)/SPECS

rpm_package_source:
	tar --transform 'flags=r;s,^,/$(RPM_SOURCE_NAME)/,' --exclude .git --exclude dist -cvjf $(RPM_SOURCE_PATH) .

rpm_build_source:
	BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ts $(RPM_SOURCE_PATH) --define "_topdir $(RPM_BUILD_DIR)"

rpm_build:
	BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ba $(RPM_SPEC_FILE) --define "_topdir $(RPM_BUILD_DIR)"
