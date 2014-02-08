# Just a hack because rpmlint rejects build with unstripped libs
%define _enable_debug_packages %{nil}
%define debug_package %{nil}

%bcond_with bootstrap

%define major 4
%define hogweedmajor 2
%define libname %mklibname nettle %{major}
%define libhogweed %mklibname hogweed %{hogweedmajor}
%define devname %mklibname -d nettle

Summary:	Nettle cryptographic library
Name:		nettle
Epoch:		1
Version:	2.7.1
Release:	2
License:	LGPLv2
Group:		System/Libraries
Url:		http://www.lysator.liu.se/~nisse/nettle/
Source0:	http://www.lysator.liu.se/~nisse/archive/%{name}-%{version}.tar.gz
Patch0:		nettle-aarch64.patch
BuildRequires:	recode
BuildRequires:	texinfo
BuildRequires:	gmp-devel
%if %{with bootstrap}
BuildRequires:	pkgconfig(openssl)
%endif

%description
Nettle is a cryptographic library that is designed to fit easily in more or
less any context:
In crypto toolkits for object-oriented languages (C++, Python, Pike, ...),
in applications like LSH or GNUPG, or even in kernel space. 

%package -n %{libname}
Group:		System/Libraries
Summary:	Nettle shared library

%description -n %{libname}
This is the shared library part of the Nettle library.

%if !%{with bootstrap}
%package -n %{libhogweed}
Group:		System/Libraries
Summary:	Hogweed shared library

%description -n %{libhogweed}
This is the shared library part of the Hogweed library.
%endif

%package -n %{devname}
Group:		Development/C++
Summary:	Header files for compiling against Nettle library
Provides:	%{name}-devel = %{EVRD}
Requires:	%{libname} = %{EVRD}
%if !%{with bootstrap}
Requires:	%{libhogweed} = %{EVRD}
%endif

%description -n %{devname}
This is the development package of nettle. Install it if you want to 
compile programs using this library.

%prep
%setup -q
%apply_patches

%build
%configure2_5x \
	--enable-shared

%make

%check
%make check

%install
%makeinstall_std
recode ISO-8859-1..UTF-8 ChangeLog

%files
%{_bindir}/*

%files -n %{libname}
%{_libdir}/libnettle.so.%{major}*

%if !%{with bootstrap}
%files -n %{libhogweed}
%{_libdir}/libhogweed.so.%{hogweedmajor}*
%endif

%files -n %{devname}
%doc AUTHORS TODO ChangeLog
%{_libdir}/libnettle.so
%if !%{with bootstrap}
%{_libdir}/libhogweed.so
%endif
%{_libdir}/*.a
%{_libdir}/pkgconfig/*.pc
%{_includedir}/nettle/
%{_datadir}/info/%{name}.info.*

