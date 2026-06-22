# Deployment — AWS ECR + EC2 via GitHub Actions

CI/CD flow: **push to `main` → GitHub builds Docker image → pushes to ECR → EC2 self-hosted runner pulls & runs it.**

```
push main ──► [GitHub cloud runner]            [EC2 self-hosted runner]
              build image ─► push to ECR ─────► pull image ─► docker run -p 8080:8080
```

Files already added: `Dockerfile`, `.dockerignore`, `.github/workflows/ci.yaml`.

---

## 0. Test the Docker image locally first

```bash
docker build -t mlproj .
docker run -p 8080:8080 mlproj
# open http://localhost:8080
```

The build runs pipeline stages 01–04 to bake `model.joblib` into the image
(because `artifacts/` is gitignored). If the build is slow/failing there, fix it
before touching AWS.

---

## 1. AWS — IAM user

1. AWS Console → **IAM** → Users → **Create user** (e.g. `mlops-deploy`).
2. Attach policies:
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonEC2FullAccess`
3. Create an **access key** (CLI use case). Save the **Access Key ID** and
   **Secret Access Key** — you'll put them in GitHub secrets.

## 2. AWS — ECR repository

1. **ECR** → **Create repository** → name it `mlproj` (private).
2. Copy the repo URI, e.g.
   `566373416292.dkr.ecr.ap-south-1.amazonaws.com/mlproj`
   - the part before `/` is the **registry** (handled automatically by the workflow)
   - the part after `/` (`mlproj`) is the **repository name** → goes in secrets.

## 3. AWS — EC2 instance

1. **EC2** → **Launch instance**: Ubuntu 22.04/24.04, `t2.medium` or larger
   (model + Docker build needs RAM), 16+ GB disk.
2. Security group inbound rules:
   - SSH (22) — your IP
   - Custom TCP **8080** — `0.0.0.0/0` (the app port)
3. SSH in and install Docker:
   ```bash
   sudo apt-get update -y && sudo apt-get upgrade -y
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

## 4. Connect EC2 as a self-hosted runner

1. GitHub repo → **Settings** → **Actions** → **Runners** → **New self-hosted runner** → Linux.
2. Run the commands GitHub shows (download, `./config.sh ...`, `./run.sh`) **on the EC2 box**.
3. When prompted for a name, use something like `self-hosted` so it matches
   `runs-on: self-hosted` in the workflow.
4. Keep it running as a service so it survives reboots:
   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

## 5. GitHub repository secrets

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name              | Value                                |
|--------------------------|--------------------------------------|
| `AWS_ACCESS_KEY_ID`      | from step 1                          |
| `AWS_SECRET_ACCESS_KEY`  | from step 1                          |
| `AWS_REGION`             | e.g. `ap-south-1`                    |
| `ECR_REPOSITORY_NAME`    | `mlproj` (the name only, not the URI) |

## 6. Deploy

```bash
git add Dockerfile .dockerignore .github/workflows/ci.yaml app.py \
        templates src/mlProject/pipeline/prediction.py DEPLOYMENT.md
git commit -m "Add prediction app + Dockerfile + ECR/EC2 CI-CD"
git push origin main
```

Watch the run under the repo's **Actions** tab. On success, open:

```
http://<EC2-public-ip>:8080
```

---

## Notes & gotchas

- **Why train in the Dockerfile?** `artifacts/` is gitignored and there's no DVC
  remote, so the model isn't in the checkout. Stages 01–04 regenerate it at build
  time. If you later add an S3 DVC remote, swap that block for `dvc pull` and add
  `dvc[s3]` to `requirements.txt`.
- **Stage 05 (MLflow eval) is intentionally not run in the image** — it needs
  tracking credentials and isn't needed to serve predictions.
- **Costs**: stop/terminate the EC2 instance and remove the runner when done to
  avoid charges. ECR storage is cheap but not free.
- **Teardown**: deregister the runner (`./config.sh remove`), terminate EC2,
  delete the ECR repo and IAM user.
```

<!-- ci: trigger run -->
<!-- ci: trigger run 2 -->
