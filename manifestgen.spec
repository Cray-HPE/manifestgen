%define install_dir /opt/cray/loftsman

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
pyinstaller --clean -y --hidden-import yamale --add-data ../manifestgen/files:manifestgen/files --add-data ../manifestgen/schemas:manifestgen/schemas -p manifestgen --onefile manifestgen/generate.py -n manifestgen --specpath dist

%install
install -m 755 -d %{buildroot}%{_bindir}
install -m 755 -d %{buildroot}%{install_dir}
install -m 755 dist/manifestgen %{buildroot}%{_bindir}/manifestgen
install -D -m 644 manifestgen/files/master_manifest.yaml %{buildroot}%{install_dir}/base_manifest.yaml

%files
%{_bindir}/manifestgen
%{install_dir}/base_manifest.yaml

%changelog