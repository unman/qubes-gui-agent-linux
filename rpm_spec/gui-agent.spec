#
# This is the SPEC file for creating binary and source RPMs for the VMs.
#
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2010  Joanna Rutkowska <joanna@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#


%{!?version: %define version %(cat version)}
# default value in case of no qubes-builder's one
%{!?backend_vmm: %define backend_vmm xen}

Name:		qubes-gui-agent
Version:	%{version}
Release:	1%{dist}
Summary:	The Qubes GUI Agent for AppVMs

Group:		Qubes
Vendor:		Invisible Things Lab
License:	GPL
URL:		http://www.qubes-os.org

Source:		.

%define pa_ver %((pkg-config --modversion libpulse 2>/dev/null || echo 0.0) | cut -d "-" -f 1)

BuildRequires:	gcc
BuildRequires:	libX11-devel
BuildRequires:	libXcomposite-devel
BuildRequires:	libXdamage-devel
BuildRequires:	libXt-devel
BuildRequires:	libtool-ltdl-devel
BuildRequires:	pulseaudio-libs-devel >= 0.9.21, pulseaudio-libs-devel <= 11.1
BuildRequires:	xorg-x11-server-devel
BuildRequires:	qubes-libvchan-%{backend_vmm}-devel
BuildRequires:	qubes-gui-common-devel >= 3.2.0
BuildRequires:	qubes-db-devel
Requires:	qubes-core-vm >= 3.0.14
Requires:	xorg-x11-xinit
Requires:	qubes-libvchan-%{backend_vmm}
Requires:	python-xcffib
Requires:   xorg-x11-server-Xorg
Provides:   qubes-gui-vm = %{version}-%{release}
Obsoletes:  qubes-gui-vm < 4.0.0


%package -n pulseaudio-qubes
Summary: Audio support for Qubes VM
# The vchan sink needs .h files from pulseaudio sources
# that are not exported by any *-devel packages; thus they are internal and
# possible to change across version. They are copied to gui git. 
# It is possible that our code will work fine with any later pulseaudio
# version; but this needs to be verified for each pulseaudio version.
Requires:	pulseaudio = %{pa_ver}
Conflicts:  qubes-gui-vm < 4.0.0

%description -n pulseaudio-qubes
 Pulseaudio module to enable sound support in Qubes VM

%define _builddir %(pwd)

%description
The Qubes GUI agent that needs to be installed in VM in order to provide the
Qubes fancy GUI.

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

rm -f pulse/pulsecore
ln -s pulsecore-%{pa_ver} pulse/pulsecore

%build
#make clean
make appvm

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT \
                     LIBDIR=%{_libdir} \
                     DATADIR=%{_datadir} \
                     PA_VER=%{pa_ver}

%post
if [ -x /bin/systemctl ] && readlink /sbin/init | grep -q systemd; then
    /bin/systemctl enable qubes-gui-agent.service 2> /dev/null
else
    chkconfig qubes-gui-agent on
fi

%post -n pulseaudio-qubes

sed -i '/^autospawn/d' /etc/pulse/client.conf
echo autospawn=no >> /etc/pulse/client.conf

%preun
if [ "$1" = 0 ] ; then
	chkconfig qubes-gui-agent off
    [ -x /bin/systemctl ] && /bin/systemctl disable qubes-gui-agent.service
    /usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :
fi

%posttrans
    /usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :

%triggerin -n pulseaudio-qubes -- pulseaudio-libs

sed -i '/^autospawn/d' /etc/pulse/client.conf
echo autospawn=no >> /etc/pulse/client.conf

%clean
rm -rf $RPM_BUILD_ROOT
rm -f %{name}-%{version}


%files
%defattr(-,root,root,-)
/usr/bin/qubes-gui
/usr/bin/qubes-session
/usr/bin/qubes-run-xorg.sh
/usr/bin/qubes-change-keyboard-layout
/usr/bin/qubes-set-monitor-layout
%{_libdir}/xorg/modules/drivers/qubes_drv.so
%{_libdir}/xorg/modules/drivers/dummyqbs_drv.so
%attr(0644,root,root) /etc/X11/xorg-qubes.conf.template
/etc/init.d/qubes-gui-agent
/etc/profile.d/qubes-gui.sh
/etc/profile.d/qubes-gui.csh
/etc/profile.d/qubes-session.sh
%config /etc/security/limits.d/90-qubes-gui.conf
%config /etc/xdg/Trolltech.conf
/etc/X11/xinit/xinitrc.d/qubes-keymap.sh
/etc/X11/xinit/xinitrc.d/20qt-x11-no-mitshm.sh
/etc/X11/xinit/xinitrc.d/20qt-gnome-desktop-session-id.sh
%config /etc/X11/Xwrapper.config
/etc/qubes-rpc/qubes.SetMonitorLayout
%config /etc/sysconfig/desktop
/etc/sysconfig/modules/qubes-u2mfn.modules
/lib/systemd/system/qubes-gui-agent.service
/usr/lib/modules-load.d/qubes-gui.conf
/usr/lib/tmpfiles.d/qubes-session.conf
/usr/lib/sysctl.d/30-qubes-gui-agent.conf
%{_datadir}/glib-2.0/schemas/20_qubes-gui-vm.gschema.override
/usr/lib/qubes/icon-sender
/etc/xdg/autostart/qubes-icon-sender.desktop
%dir /var/log/qubes

%files -n pulseaudio-qubes
/usr/lib/tmpfiles.d/qubes-pulseaudio.conf
/etc/pulse/qubes-default.pa
/usr/bin/start-pulseaudio-with-vchan
%{_libdir}/pulse-%{pa_ver}/modules/module-vchan-sink.so
/etc/xdg/autostart/qubes-pulseaudio.desktop
