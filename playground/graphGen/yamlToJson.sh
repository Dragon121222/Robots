
#!/bin/bash

python3 -c "import yaml,json,sys; print(json.dumps(yaml.safe_load(sys.stdin)))" < $1 > $2