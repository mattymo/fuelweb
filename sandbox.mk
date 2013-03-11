define yum_local_repo
[mirror]
name=Mirantis mirror
baseurl=file://$(shell readlink -f -m $(LOCAL_MIRROR_CENTOS_OS_BASEURL))
gpgcheck=0
enabled=1
endef

SANDBOX_PACKAGES:=\
	byacc \
	flex \
	gcc \
	glibc-devel \
	glibc-headers \
	kernel-headers \
	make \
	python-devel.x86_64 \
	python-pip \
	rpm-build \
	tar \
	postgresql-devel \


define SANDBOX_UP
mkdir -p $(SANDBOX)/etc/yum.repos.d
cp /etc/resolv.conf $(SANDBOX)/etc/resolv.conf
cat > $(SANDBOX)/etc/yum.repos.d/base.repo <<EOF
$(yum_local_repo)
EOF
rpm -i --root=$(SANDBOX) `find $(LOCAL_MIRROR_CENTOS_OS_BASEURL) -name "centos-release*rpm" | head -1` || \
echo "centos-release already installed"
rm -f $(SANDBOX)/etc/yum.repos.d/Cent*
rpm --root=$(SANDBOX) --rebuilddb
yum --installroot=$(SANDBOX) -y --nogpgcheck install $(SANDBOX_PACKAGES)
mount | grep -q $(SANDBOX)/proc || sudo mount --bind /proc $(SANDBOX)/proc
mount | grep -q $(SANDBOX)/dev || sudo mount --bind /dev $(SANDBOX)/dev
endef

define SANDBOX_DOWN
sync
umount $(SANDBOX)/proc
umount $(SANDBOX)/dev
endef
