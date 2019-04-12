Name: manifestgen
License: Cray Software License Agreement
Summary: Cray Command Line Tool
Version: %(cat ./build_version)
Release: 1
Vendor: Cray Inc.
Group: Cloud
Source: %{name}-%{version}.tar.gz

%description
A CLI tool to generate a loftsman manifest from a blob

%prep
%setup -q

%build
pyinstaller --clean -y --hidden-import yamale --add-data ../build_version:manifestgen --add-data ../manifestgen/files:manifestgen/files --add-data ../manifestgen/schemas:manifestgen/schemas -p manifestgen --onefile manifestgen/generate.py -n manifestgen --specpath dist

%install
mkdir -p %{buildroot}%{_bindir}
install -m 755 dist/manifestgen %{buildroot}%{_bindir}/manifestgen

%files
%{_bindir}/manifestgen

%changelog