pkgname=python-rbackup
pkgver=0.7
pkgrel=1
pkgdesc="rsync-based backup-tool"
arch=(any)
#url=""
license=('custom')
#groups=()
#depends=('python', 'rsync')
#makedepends=()
#provides=()
#conflicts=()
#replaces=()
#backup=()
options=(!emptydirs)
#install=
#source=()
#md5sums=()

package() {
  cd $srcdir/..
  #cd "$srcdir/$pkgname-$pkgver"
  python setup.py install --root="$pkgdir/" --optimize=1
  mkdir -p $pkgdir/etc/rbackup
  mkdir -p $pkgdir/etc/rbackup/prescripts
  mkdir -p $pkgdir/etc/rbackup/postscripts
  #cp sample.conf $pkgdir/etc/rbackup/rbackup.conf
}

# vim:set ts=2 sw=2 et:
