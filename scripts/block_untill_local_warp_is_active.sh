tries=$1

if [ -z $tries ]; then
    tries=30
fi

for i in {1..$tries}; do
    sleep 1
    RESULT=$(curl -s --max-time 10 --socks5-hostname 127.0.0.1:1080 https://cloudflare.com/cdn-cgi/trace 2>/dev/null || echo "failed")
    if echo "$RESULT" | grep -qE "warp=(on|plus)"; then
        echo "✅ WARP is active!"
        echo "$RESULT"
        exit 0
    fi
done

exit 1