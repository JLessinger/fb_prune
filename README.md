Clean up your Facebook profile. Maintain control.

fb-prune is a (soon-to-be) open source tool for finding material on your Facebook that you'd like to remove.
You don't need to give any third party access to your account other than Facebook's own Graph Explorer tool.

For good security reasons, but unfortunately for our purposes, you will need to manually delete unwanted content.
This tool can only help you find it.

Intended workflow:

1. Get an access token with maximal access from Facebook Graph Explorer
2. Run script to download all your relevant Facebook data.
3. [NOT YET IMPLEMENTED] "Tinder swipe" through your content to decide which should be deleted.
4. A list of ids for unwanted content will be produced. Delete manually.

(1) and (4) could be automated with browser simulation.
	
installation:
	1. Clone repo
	2. Install dependencies (e.g. with pip)
	3. Run tests:
	  ` $ python -m unittest fb_prune_tests`

dependencies:
	python 2.7
	facepy
	argparse
	
usage examples: 
`$ python fb_prune.py my_access_token`
`$ python fb_prune.py --debug my_access_token 1> my_json.txt 2> debug_info.txt`
`$ python fb_prune.py --max-depth 1 --page-limit 25 my_access_token`
`$ python fb_prune.py --excludes friends request_history my_access_token`
`$ python fb_prune.py -h # for full help message`

license: TODO

contribute: TODO