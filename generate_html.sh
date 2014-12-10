echo "<!DOCTYPE html>"
echo "<html>"
echo "<body"
echo "<h1> Cluster performance metrics </h1>"

for f in *.png; do
  echo "<img src=\"$f\">"
done

echo "</body>"
echo "</html>"
