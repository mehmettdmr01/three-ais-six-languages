package main

import (
	"fmt"
	"math/bits"
	"os"
	"strconv"
	"time"
)

func main() {
	n, _ := strconv.Atoi(os.Args[1])
	gens, _ := strconv.Atoi(os.Args[2])
	buf, err := os.ReadFile(os.Args[3])
	if err != nil {
		os.Exit(1)
	}
	w := (n + 63) / 64
	l := uint(n - 64*(w-1))
	lm := ^uint64(0)
	if l != 64 {
		lm = (uint64(1) << l) - 1
	}
	cur := make([]uint64, n*w)
	nxt := make([]uint64, n*w)
	we := make([]uint64, n*w)
	ee := make([]uint64, n*w)
	k := 0
	for _, c := range buf {
		if k >= n*n {
			break
		}
		if c == '1' {
			r, q := k/n, k%n
			cur[r*w+q/64] |= uint64(1) << uint(q%64)
			k++
		} else if c == '0' {
			k++
		}
	}
	t0 := time.Now()
	for g := 0; g < gens; g++ {
		for r := 0; r < n; r++ {
			row := cur[r*w : (r+1)*w]
			wr := we[r*w : (r+1)*w]
			er := ee[r*w : (r+1)*w]
			for i := 0; i < w; i++ {
				x := row[i]
				var e, wv uint64
				if i < w-1 {
					e = (x >> 1) | (row[i+1] << 63)
				} else {
					e = (x >> 1) | ((row[0] & 1) << (l - 1))
				}
				if i > 0 {
					wv = (x << 1) | (row[i-1] >> 63)
				} else {
					wv = (x << 1) | ((row[w-1] >> (l - 1)) & 1)
				}
				if i == w-1 {
					wv &= lm
				}
				wr[i] = wv
				er[i] = e
			}
		}
		for r := 0; r < n; r++ {
			ru := r - 1
			if r == 0 {
				ru = n - 1
			}
			rd := r + 1
			if r == n-1 {
				rd = 0
			}
			uw := we[ru*w : (ru+1)*w]
			ue := ee[ru*w : (ru+1)*w]
			uc := cur[ru*w : (ru+1)*w]
			mw := we[r*w : (r+1)*w]
			me := ee[r*w : (r+1)*w]
			mc := cur[r*w : (r+1)*w]
			dw := we[rd*w : (rd+1)*w]
			de := ee[rd*w : (rd+1)*w]
			dc := cur[rd*w : (rd+1)*w]
			o := nxt[r*w : (r+1)*w]
			for i := 0; i < w; i++ {
				a, b, c := uw[i], uc[i], ue[i]
				s1 := a ^ b ^ c
				c1 := (a & b) | (c & (a ^ b))
				d, e := mw[i], me[i]
				s2 := d ^ e
				c2 := d & e
				a, b, c = dw[i], dc[i], de[i]
				s3 := a ^ b ^ c
				c3 := (a & b) | (c & (a ^ b))
				on := s1 ^ s2 ^ s3
				k1 := (s1 & s2) | (s3 & (s1 ^ s2))
				par := c1 ^ c2 ^ c3 ^ k1
				two := (c1 & c2) | (c3 & k1) | ((c1 | c2) & (c3 | k1))
				o[i] = par &^ two & (on | mc[i])
			}
		}
		cur, nxt = nxt, cur
	}
	ms := float64(time.Since(t0).Nanoseconds()) / 1e6
	alive := 0
	for _, x := range cur {
		alive += bits.OnesCount64(x)
	}
	fmt.Printf("alive=%d sim_ms=%.3f\n", alive, ms)
}
