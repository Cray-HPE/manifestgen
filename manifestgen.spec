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
%global __python /usr/bin/python3
%global __pyinstaller /usr/bin/pyinstaller
%define install_dir /opt/cray/loftsman

Name: manifestgen
License: MIT License
Summary: Cray Command Line Tool
Version: %(echo ${VERSION})
Release: 1
Vendor: Cray Inc.
Group: Cloud
Source: %{name}-%{version}.tar.gz

%description
A CLI tool to generate a loftsman manifest from a blob

%prep
%setup -q

%build
%{__python} -m pip install -U pyinstaller
%{__python} -m pip install -q build
%{__python} -m build

%{__python} setup.py install

%{__pyinstaller} --clean -y --hidden-import='pkg_resources.py2_warn' --hidden-import yamale --add-data ../manifestgen/schemas:manifestgen/schemas -p manifestgen --onefile manifestgen/generate.py -n manifestgen --specpath dist

%install
install -m 755 -d %{buildroot}%{_bindir}
install -m 755 -d %{buildroot}%{install_dir}
install -m 755 dist/manifestgen %{buildroot}%{_bindir}/manifestgen

%files
%{_bindir}/manifestgen
%license LICENSE

%changelog
