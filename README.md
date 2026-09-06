# FMML

A freelance work search agent: pulls listings from a few sources (Remotive,
RemoteOK, WeWorkRemotely, Freelancer.com, plus manually pasted-in Upwork/
Fiverr posts), scores them against your skills, and ranks the best matches.

See [SETUP.md](SETUP.md) for installation, configuration, and how to run it
daily with an email digest.

```bash
python3 -m pip install -r requirements.txt
python3 -m freelance_agent.cli
```
