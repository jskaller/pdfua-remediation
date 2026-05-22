import os
import shutil

TARGET_DIR = "montefiore-pdfua-remediation-box"
WORKSPACE = os.path.join(TARGET_DIR, "workspace")
SKILL_DIR = os.path.join(WORKSPACE, "skills", "montefiore-pdfua-unified-v6")
TOOLS_DIR = os.path.join(WORKSPACE, "tools")

def setup_structure():
    print("Creating OpenClaw unified directory structure...")
    os.makedirs(TOOLS_DIR, exist_ok=True)
    os.makedirs(os.path.join(WORKSPACE, "templates"), exist_ok=True)
    os.makedirs(os.path.join(WORKSPACE, "assets", "validation_profiles"), exist_ok=True)
    os.makedirs(os.path.join(WORKSPACE, "examples"), exist_ok=True)

def migrate_files():
    print("Migrating rules and checklists...")
    src_rules = "montefiore_pdfua_quickstart_v6_01_rules"
    if os.path.exists(src_rules):
        shutil.copytree(os.path.join(src_rules, "rules"), os.path.join(SKILL_DIR, "rules"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(src_rules, "checklists"), os.path.join(SKILL_DIR, "checklists"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(src_rules, "prompts"), os.path.join(SKILL_DIR, "prompts"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(src_rules, "docs"), os.path.join(SKILL_DIR, "docs"), dirs_exist_ok=True)

    print("Migrating Python scripts and repair helpers...")
    src_scripts = "montefiore_pdfua_quickstart_v6_02_scripts"
    if os.path.exists(src_scripts):
        shutil.copytree(os.path.join(src_scripts, "repair_helpers"), os.path.join(TOOLS_DIR, "repair_helpers"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(src_scripts, "scripts"), os.path.join(TOOLS_DIR, "scripts"), dirs_exist_ok=True)
        if os.path.exists(os.path.join(src_scripts, "requirements.txt")):
            shutil.copy(os.path.join(src_scripts, "requirements.txt"), os.path.join(TARGET_DIR, "requirements.txt"))

    print("Migrating master skill orchestrator...")
    src_skills = "montefiore_pdfua_quickstart_v6_03_skills"
    skill_md_source = os.path.join(src_skills, "skills", "montefiore-pdfua-unified-v6", "SKILL.md")
    if os.path.exists(skill_md_source):
        shutil.copy(skill_md_source, os.path.join(SKILL_DIR, "SKILL.md"))

    print("Migrating reference archives and static assets...")
    src_assets = "montefiore_pdfua_quickstart_v6_05_assets"
    if os.path.exists(src_assets):
        shutil.copytree(os.path.join(src_assets, "validation_profiles"), os.path.join(WORKSPACE, "assets", "validation_profiles"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(src_assets, "templates"), os.path.join(WORKSPACE, "templates"), dirs_exist_ok=True)

    src_examples = "montefiore_pdfua_quickstart_v6_04_examples_reference_readonly"
    if os.path.exists(src_examples):
        shutil.copytree(src_examples, os.path.join(WORKSPACE, "examples"), dirs_exist_ok=True)

def write_configs():
    print("Generating Dockerfile and OpenClaw configuration overlays...")
    openclaw_json = """{
  "model": "gpt-4o",
  "temperature": 0.0,
  "workspace_dir": "./workspace",
  "allowed_commands": ["python3", "bash", "qpdf", "java"],
  "env": {
    "OPENAI_API_KEY": "${OPENAI_API_KEY}"
  }
}"""
    with open(os.path.join(TARGET_DIR, "openclaw.json"), "w") as f:
        f.write(openclaw_json)

    dockerfile = """FROM nikolaik/python-nodejs:python3.11-nodejs20-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN apt-get update && apt-get install -y --no-install-recommends \\
    openjdk-17-jre-headless \\
    qpdf \\
    bash \\
    curl \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN npm install -g openclaw

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY openclaw.json ./
COPY workspace/ ./workspace/

RUN chmod +x ./workspace/tools/scripts/*.sh 2>/dev/null || true

EXPOSE 18789
CMD ["openclaw", "run"]"""
    with open(os.path.join(TARGET_DIR, "Dockerfile"), "w") as f:
        f.write(dockerfile)

if __name__ == "__main__":
    setup_structure()
    migrate_files()
    write_configs()
    print("\\n[SUCCESS] Pipeline consolidated inside project directory!")
