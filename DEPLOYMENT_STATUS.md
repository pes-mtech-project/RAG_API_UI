# Final Setup Instructions

## Current Status ✅
- AWS Configuration: ✅ Configured
- EC2 Instance: ✅ Running at 3.7.194.20 (i-05cf3774f0646b47d)
- SSH Key: ✅ Generated and stored locally
- GitHub Workflows: ✅ Created

## Next Steps

### 1. Add GitHub Secrets
Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these Repository Secrets:

**EC2_INSTANCE_ID**
```
i-05cf3774f0646b47d
```

**EC2_HOST**
```
3.7.194.20
```

**EC2_SSH_PRIVATE_KEY**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4Jk5q7ieoV+3u2DNVSdI9jK2RsgDVQjpZ++47potSZhw7Wuu
Q3iX9nv7GgLuVv3b5Dfc8NIkLV04GgDXTKu15+pr8/NAnSJtnJINGgwCYyl7/kdt
0Ia4VQ/8vy+2hL0l0Mz/jtfnStU1EUnwpF1eZ116fprSSwWhYeOnWvTEtZY+sBdE
1Rb+r3XKSAxgFvl3MFBQktaab804lZO4Sdshp/S/Jb+1UrasSkyacNCfe2vge9DO
2Htp+fuQgPli4k4n1XEvaHRWaLWe2/9C3ECEmhU52PuKE+HLy/admrWnm0cw41o/
lRIsKuXkQxBszV87EXcw0em98cGHpu2QG7EaVwIDAQABAoIBAQC0q62PrJi2uZfD
/K/QMyTnH44vTBAaJGwVtuotzgpmLGGTK07oaabcmYk5uGffxKBRanqponGFqHpL
uKd4vpw67gFfISu1+47vJzGw5T46ZJGgz/bPir/XdV/cr9YD22ADIhTl5FnjgbUJ
rlAM+CrLvY+fLo3B2cqjQw1KBqICa1Mh9PqLqdeP8s+AI+/2cTgQM8eduFYsATH4
DFDCQWKaO2Y6FiwcmP2ImV8Uk2VNVIM8UIu/UThYseHWLtZJgScDWGd4Ih7ZrEKM
9kct6jM/89wzxPKtMoC2Ltsnqmsrb8uU4U+T8hKHdTbDgJMkfRhYU2gVtA8j1eVu
WT6bikUBAoGBAPYxx5lKehPj23TU8v3wR+ZoPPzTGXx17k6OGzy7B/x7aG+go01o
TZo6fy9emk8zpmJi915EWu8ijjy6hSzWgjtpgXLy2cFHPmSZxN2l9whMBugvSn5J
IPiLdHJX7BkqNJb01cxQcwRWpkuQbOfAUNHNgTJvzLozAqdJ+gNFsfCBAoGBAOmL
QHG895TK+sBEDYAcRFzjlIyeh3vb6afXdCqqPF++SM0bTFe93c+6D8fvsGM0jDbN
lptzy9U0vNI39AqS+BXyeRPUYQys1Jxn4ILmelmbx4xAYpOsxtPcSfg49MUp9mhb
6tDk4kCo5pdKfK3IQtisUi0/UeMFfxPukpyAkR7XAoGBAJsmceg71EU2onW1QdEg
nN8qL80Q6A3UcDMXQTj7kSPfTciTTnaY1dbtKHvcvZhOL3vvbH7+yuPLPiItVYIV
SQtSCR88xlgUotBZS4R3c//Jkcy/CM4fHeUkVWU93W9adrvvXdEdne5NAQ273bYL
L6OYQ+RaKoXpYbG1YBax1FqBAoGAICAWmk6rI92UBpSV4tSAluJ7UaiQ7HnAt2TM
xv2p1mW/b+9cXglxFJz8hL0030CgNP2sxO91z3s0qhomSLoUxDgZbZ/eRbcUe/tS
B8+abu8d0O4eYT/4DbaUuj9jdCekjJBwSZHiiZByP8dwRRtyDooNt8mpAviDlYNQ
yZRp4fsCgYBGLPbcJb4LDXqtImEh/QM7nbgnfnf6OBNAFfJZkUko/7tJyxvH3wxt
UShMmN6PNXI1xJvWJbIM+ZZRhrk7WlI+nQQmErpagIWCoDJRmc7Vm1P5J8gbUCy4
uns3EkQTfxT+hbFM0a8SnINDTwM/hrEjXAdAl81yfhVJE7ubjscCAA==
-----END RSA PRIVATE KEY-----
```

### 2. Manual SSH Connection Test

Try connecting manually first to add the SSH key to the EC2 instance:

```bash
# Connect to EC2 (this may fail initially)
ssh -i ~/.ssh/finbert-aws ec2-user@3.7.194.20

# If connection fails, we'll need to add the public key manually
```

### 3. Alternative: Add SSH Key via EC2 Instance Connect

If manual SSH fails, we can use EC2 Instance Connect:

```bash
# Send public key via EC2 Instance Connect
aws ec2-instance-connect send-ssh-public-key \
    --instance-id i-05cf3774f0646b47d \
    --availability-zone ap-south-1a \
    --instance-os-user ec2-user \
    --ssh-public-key file://~/.ssh/finbert-aws.pub \
    --region ap-south-1
```

### 4. Test Deployment

Once SSH access is working, trigger the deployment:

1. Go to GitHub Actions
2. Run the "Deploy to AWS" workflow
3. Monitor the deployment logs

### 5. Access Your Application

After successful deployment:
- **API**: http://3.7.194.20:8000
- **Streamlit UI**: http://3.7.194.20:8501

## Current Files Created:
- ✅ `.github/workflows/deploy.yml` - Main deployment workflow
- ✅ `.github/workflows/infrastructure.yml` - Infrastructure management
- ✅ `.github/workflows/development.yml` - Development checks
- ✅ `CI_CD_SETUP_GUIDE.md` - Complete setup documentation
- ✅ `setup-ssh-key.sh` - SSH key setup script

## Troubleshooting:
- If SSH fails, check security group allows port 22
- If deployment fails, check GitHub secrets are correctly set
- If services don't start, check EC2 instance logs via AWS Console