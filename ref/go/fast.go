// Same algorithm as c/fast.c: the wrap is handled only for the first and last column. Re-slicing to the
// same length lets the compiler drop bounds checks. c|m == 3 is the rule without a second comparison;
// the compiler turns the if into a conditional set, so there is no branch to mispredict.
package main

import (
	"bytes"
	"fmt"
	"os"
	"strconv"
	"time"
)

func rule(c, m byte) byte {
	var r byte
	if c|m == 3 {
		r = 1
	}
	return r
}

func step(n int, cur, next []byte) {
	for y := 0; y < n; y++ {
		ui, di := y-1, y+1
		if y == 0 {
			ui = n - 1
		}
		if y == n-1 {
			di = 0
		}
		u, m, d := cur[ui*n:ui*n+n], cur[y*n:y*n+n], cur[di*n:di*n+n]
		o := next[y*n : y*n+n]
		u, d, o = u[:len(m)], d[:len(m)], o[:len(m)]
		for x := 1; x < len(m)-1; x++ {
			c := u[x-1] + u[x] + u[x+1] + m[x-1] + m[x+1] + d[x-1] + d[x] + d[x+1]
			o[x] = rule(c, m[x])
		}
		o[0] = rule(u[n-1]+u[0]+u[1]+m[n-1]+m[1]+d[n-1]+d[0]+d[1], m[0])
		o[n-1] = rule(u[n-2]+u[n-1]+u[0]+m[n-2]+m[0]+d[n-2]+d[n-1]+d[0], m[n-1])
	}
}

func main() {
	n, _ := strconv.Atoi(os.Args[1])
	gens, _ := strconv.Atoi(os.Args[2])
	text, err := os.ReadFile(os.Args[3])
	if err != nil {
		panic(err)
	}
	text = bytes.ReplaceAll(text, []byte("\n"), nil)
	cur, next := make([]byte, n*n), make([]byte, n*n)
	for i, b := range text {
		if b == '1' {
			cur[i] = 1
		}
	}
	t0 := time.Now()
	for g := 0; g < gens; g++ {
		step(n, cur, next)
		cur, next = next, cur
	}
	sim := time.Since(t0).Seconds() * 1e3
	alive := 0
	for _, b := range cur {
		alive += int(b)
	}
	fmt.Printf("alive=%d sim_ms=%.3f\n", alive, sim)
}
