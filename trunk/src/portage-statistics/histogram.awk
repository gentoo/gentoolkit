{
	match($0, "<([A-Za-z0-9.-]+@[A-Za-z0-9.-]+)>") 
	val=substr($0, RSTART, RLENGTH)
	arr[val]++
	total++
}

END {
	for (x in arr) {
		printf("%35s: %-4d of %-4d (%-4.2f%)\n",x,arr[x],total,arr[x]*100/total)
		mytot += arr[x]
	}
	printf("%35s: %-4d of %-4d (%-4.2f%)\n","TOTAL",mytot, total,mytot*100/total)
}