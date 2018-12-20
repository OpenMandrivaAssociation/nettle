# Just a hack because rpmlint rejects build with unstripped libs
#% define _enable_debug_packages %{nil}
#% define debug_package %{nil}
%define _disable_lto 1

%global optflags %{optflags} -Ofast

%bcond_with bootstrap

%define major 6
%define hogweedmajor 4
%define libname %mklibname nettle %{major}
%define libhogweed %mklibname hogweed %{hogweedmajor}
%define devname %mklibname -d nettle

Summary:	Nettle cryptographic library
Name:		nettle
Epoch:		1
Version:	3.4.1
Release:	1
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.lysator.liu.se/~nisse/nettle/
Source0:	http://www.lysator.liu.se/~nisse/archive/%{name}-%{version}.tar.gz
BuildRequires:	recode
BuildRequires:	gmp-devel
BuildRequires:	texinfo
%if %{with bootstrap}
BuildRequires:	pkgconfig(openssl)
%endif

%description
Nettle is a cryptographic library that is designed to fit easily in more or
less any context:
In crypto toolkits for object-oriented languages (C++, Python, Pike, ...),
in applications like LSH or GNUPG, or even in kernel space.

%files
%{_bindir}/*

#----------------------------------------------------------------------------

%package -n %{libname}
Summary:	Nettle shared library
Group:		System/Libraries

%description -n %{libname}
This is the shared library part of the Nettle library.

%files -n %{libname}
%{_libdir}/libnettle.so.%{major}*

#----------------------------------------------------------------------------

%if !%{with bootstrap}
%package -n %{libhogweed}
Summary:	Hogweed shared library
Group:		System/Libraries

%description -n %{libhogweed}
This is the shared library part of the Hogweed library.

%files -n %{libhogweed}
%{_libdir}/libhogweed.so.%{hogweedmajor}*
%endif

#----------------------------------------------------------------------------

%package -n %{devname}
Summary:	Header files for compiling against Nettle library
Group:		Development/C++
Provides:	%{name}-devel = %{EVRD}
Requires:	%{libname} = %{EVRD}
%if !%{with bootstrap}
Requires:	%{libhogweed} = %{EVRD}
%endif

%description -n %{devname}
This is the development package of nettle. Install it if you want to 
compile programs using this library.

%files -n %{devname}
%doc AUTHORS TODO ChangeLog
%{_libdir}/libnettle.so
%if !%{with bootstrap}
%{_libdir}/libhogweed.so
%endif
%{_libdir}/*.a
%{_libdir}/pkgconfig/*.pc
%{_includedir}/nettle/
%{_infodir}/nettle.*

#----------------------------------------------------------------------------

%prep
%autosetup -p1
# Disable -ggdb3 which makes debugedit unhappy
sed s/ggdb3/g/ -i configure
#sed 's/ecc-192.c//g' -i Makefile.in
#sed 's/ecc-224.c//g' -i Makefile.in

%build
mkdir -p bfd
ln -s %{_bindir}/ld.bfd bfd/ld
export PATH=$PWD/bfd:$PATH
%ifarch %{ix86} x86_64
CFLAGS="%optflags -fno-integrated-as"
%endif
%configure \
	--enable-static \
	--disable-openssl \
%ifarch %{x86_64}
	--enable-x86-aesni \
%endif
	--enable-shared

%make_build

%check
%make check

%install
%make_install
recode ISO-8859-1..UTF-8 ChangeLog
