# nettle is used by gnutls, gnutls is used by wine
%ifarch %{x86_64}
%bcond_without compat32
%endif

%global optflags %{optflags} -O3

%bcond_with bootstrap

# (tpg) enable PGO build
%bcond_without pgo

%define major 8
%define hogweedmajor 6
%define libname %mklibname nettle %{major}
%define libhogweed %mklibname hogweed %{hogweedmajor}
%define devname %mklibname -d nettle
%define lib32name %mklib32name nettle %{major}
%define lib32hogweed %mklib32name hogweed %{hogweedmajor}
%define dev32name %mklib32name -d nettle

Summary:	Nettle cryptographic library
Name:		nettle
Epoch:		1
Version:	3.8.1
Release:	2
License:	LGPLv2+
Group:		System/Libraries
Url:		http://www.lysator.liu.se/~nisse/nettle/
Source0:	https://ftp.gnu.org/gnu/nettle/%{name}-%{version}.tar.gz
BuildRequires:	recode
BuildRequires:	gmp-devel
BuildRequires:	texinfo
%ifnarch riscv64
BuildRequires:	pkgconfig(valgrind)
%endif
%if %{with bootstrap}
BuildRequires:	pkgconfig(openssl)
%endif
%if %{with compat32}
BuildRequires:	devel(libgmp)
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
%doc AUTHORS ChangeLog
%{_libdir}/libnettle.so
%if !%{with bootstrap}
%{_libdir}/libhogweed.so
%endif
%{_libdir}/*.a
%{_libdir}/pkgconfig/*.pc
%{_includedir}/nettle/
%doc %{_infodir}/nettle.*

#----------------------------------------------------------------------------

%if %{with compat32}
%package -n %{lib32name}
Summary:	Nettle shared library (32-bit)
Group:		System/Libraries

%description -n %{lib32name}
This is the shared library part of the Nettle library.

%files -n %{lib32name}
%{_prefix}/lib/libnettle.so.%{major}*

#----------------------------------------------------------------------------

%if !%{with bootstrap}
%package -n %{lib32hogweed}
Summary:	Hogweed shared library (32-bit)
Group:		System/Libraries

%description -n %{lib32hogweed}
This is the shared library part of the Hogweed library.

%files -n %{lib32hogweed}
%{_prefix}/lib/libhogweed.so.%{hogweedmajor}*
%endif

#----------------------------------------------------------------------------

%package -n %{dev32name}
Summary:	Header files for compiling against Nettle library (32-bit)
Group:		Development/C++
Requires:	%{devname} = %{EVRD}
Requires:	%{lib32name} = %{EVRD}
%if !%{with bootstrap}
Requires:	%{lib32hogweed} = %{EVRD}
%endif

%description -n %{dev32name}
This is the development package of nettle. Install it if you want to 
compile programs using this library.

%files -n %{dev32name}
%{_prefix}/lib/libnettle.so
%if !%{with bootstrap}
%{_prefix}/lib/libhogweed.so
%endif
%{_prefix}/lib/pkgconfig/*.pc
%{_prefix}/lib/*.a
%endif

%prep
%autosetup -p1
%config_update
# Disable -ggdb3 which makes debugedit unhappy
sed s/ggdb3/g/ -i configure
#sed 's/ecc-192.c//g' -i Makefile.in
#sed 's/ecc-224.c//g' -i Makefile.in

%build
export CONFIGURE_TOP="$(pwd)"
%if %{with compat32}
mkdir build32
cd build32
# FIXME Without --enable-mini-gmp, "make check" fails a number of tests,
# but gmp itself seems to be working (make check in gmp succeeds flawlessly).
# This may need further analysis; until we've figured out the right thing
# to do, --enable-mini-gmp is an ok workaround.
# This should be checked again with every gmp and/or nettle update.
# In 64-bit configurations, not using mini-gmp works fine.
%configure32 \
	--enable-x86-aesni \
	--enable-mini-gmp \
%ifnarch znver1
	--enable-fat \
%endif
	--enable-static
%make_build
cd ..
%endif

mkdir -p bfd
ln -s %{_bindir}/ld.bfd bfd/ld
export PATH=$PWD/bfd:$PATH

# enable-x86-aesni without enable-fat likely causes bug 2408

mkdir build
cd build

%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=8" \
CXXFLAGS="%{optflags} -fprofile-generate" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%configure \
	--enable-static \
	--disable-openssl \
%ifarch %{arm} %{aarch64}
	--enable-arm-neon \
%endif
%ifarch %{x86_64}
	--enable-x86-aesni \
%ifnarch znver1
	--enable-fat \
%endif
%endif
	--enable-shared

%make_build
make check ||:

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw

make clean

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%configure \
	--enable-static \
	--disable-openssl \
	--disable-x86-sha-ni \
%ifarch %{arm} %{aarch64}
	--enable-arm-neon \
%endif
%ifarch %{x86_64}
	--enable-x86-aesni \
%ifnarch znver1
	--enable-fat \
%endif
%endif
	--enable-shared

%make_build

%if ! %{cross_compiling}
%check
%if %{with compat32}
%make_build check -C build32
%endif
%make_build check -C build
%endif

%install
%if %{with compat32}
%make_install -C build32
%endif
%make_install -C build
recode ISO-8859-1..UTF-8 ChangeLog
