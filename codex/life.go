package main

import ("fmt"; "os"; "strconv"; "time")

var rule = [18]byte{0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0}

func halo(a []byte, n, s int) {
	for i:=1; i<=n; i++ { r:=i*s; a[r]=a[r+n]; a[r+n+1]=a[r+1] }
	copy(a[:s], a[n*s:n*s+s]); copy(a[(n+1)*s:(n+2)*s], a[s:2*s])
}
func step(a, b []byte, n, s int) uint64 {
	var live uint64
	for i:=1; i<=n; i++ { k:=i*s+1; for j:=1; j<=n; j,k=j+1,k+1 {
		x:=a[k-s-1]+a[k-s]+a[k-s+1]+a[k-1]+a[k+1]+a[k+s-1]+a[k+s]+a[k+s+1]
		v:=rule[int(x)<<1|int(a[k])]; b[k]=v; live+=uint64(v)
	} }
	return live
}
func main() {
	if len(os.Args)!=4 { return }; n,_:=strconv.Atoi(os.Args[1]); gens,_:=strconv.Atoi(os.Args[2]); if n<=0 { return }
	s:=n+2; a:=make([]byte,s*s); b:=make([]byte,s*s); data,_:=os.ReadFile(os.Args[3]); q:=0
	for i:=1;i<=n;i++ { for j:=1;j<=n;j++ { for data[q]=='\n'||data[q]=='\r' {q++}; if data[q]=='1' {a[i*s+j]=1}; q++ } }
	start:=time.Now(); var live uint64
	if gens==0 { for i:=1;i<=n;i++ { for j:=1;j<=n;j++ {live+=uint64(a[i*s+j])} } }
	for g:=0;g<gens;g++ { halo(a,n,s); live=step(a,b,n,s); a,b=b,a }
	fmt.Printf("alive=%d sim_ms=%.3f\n",live,float64(time.Since(start).Nanoseconds())/1e6)
}
