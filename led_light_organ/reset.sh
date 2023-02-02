#/bin/bash

#line=1

echo "reset"
for i in {4..27}; do
  pigs p $i 0
done
