pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 60, unit: 'MINUTES')
  }

  parameters {
    choice(
      name: 'DEPLOY_ENV',
      choices: ['staging', 'production'],
      description: 'Target environment for deploy'
    )
    booleanParam(
      name: 'SKIP_DEPLOY',
      defaultValue: false,
      description: 'Build and test only — skip deploy stage'
    )
    string(
      name: 'PUBLIC_APP_URL',
      defaultValue: 'https://play.doxstation.com',
      description: 'Browser-facing tutor UI URL (use https://play.doxstation.com after DNS + TLS)'
    )
    string(
      name: 'ENV_CREDENTIAL_ID',
      defaultValue: 'ai-code-player-env-file',
      description: 'Jenkins Secret file credential ID. Must match Manage Jenkins → Credentials → ID (not the uploaded filename).'
    )
  }

  environment {
    APP_NAME             = 'ai-code-player'
    API_IMAGE            = "ai-coder-api:${env.BUILD_NUMBER}"
    API_IMAGE_LATEST     = 'ai-coder-api:latest'
    WEB_IMAGE            = "ai-coder-web:${env.BUILD_NUMBER}"
    WEB_IMAGE_LATEST     = 'ai-coder-web:latest'
    RUNNER_IMAGE         = "ai-coder-runner:${env.BUILD_NUMBER}"
    RUNNER_IMAGE_LATEST  = 'ai-coder-runner:latest'
    COMPOSE_PROJECT_NAME = 'aicoder'
    API_HOST_PORT        = '8010'
    WEB_HOST_PORT        = '3010'
    RUNNER_HOST_PORT     = '8090'
    POSTGRES_HOST_PORT   = '5433'
    REDIS_HOST_PORT      = '6380'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          echo "Branch: ${GIT_BRANCH:-unknown}"
          echo "Commit: ${GIT_COMMIT:-unknown}"
          git rev-parse --short HEAD || true
          echo "=== Workspace files ==="
          ls -la
          test -f Jenkinsfile || { echo "ERROR: Jenkinsfile missing from git checkout"; exit 1; }
          test -f docker-compose.yml || { echo "ERROR: docker-compose.yml missing"; exit 1; }
          test -f backend/Dockerfile || { echo "ERROR: backend/Dockerfile missing"; exit 1; }
          test -f frontend/Dockerfile || { echo "ERROR: frontend/Dockerfile missing"; exit 1; }
          test -f services/code-runner/Dockerfile || { echo "ERROR: code-runner Dockerfile missing"; exit 1; }
          test -f backend/scripts/jenkins_smoke.py || { echo "ERROR: jenkins_smoke.py missing"; exit 1; }
          test -f scripts/normalize_deploy_env.py || { echo "ERROR: normalize_deploy_env.py missing"; exit 1; }
          test -f ai-code-player.env.example || { echo "ERROR: ai-code-player.env.example missing"; exit 1; }
          test -f scripts/install_host_nginx.sh || { echo "ERROR: scripts/install_host_nginx.sh missing"; exit 1; }
          test -f deploy/host-nginx-aicoder.conf || { echo "ERROR: deploy/host-nginx-aicoder.conf missing"; exit 1; }
          test -f deploy/host-nginx-aicoder.http.conf || { echo "ERROR: deploy/host-nginx-aicoder.http.conf missing"; exit 1; }
        '''
      }
    }

    stage('Detect Tools') {
      steps {
        sh '''
          echo "=== Agent tools ==="
          docker --version
          docker compose version
          python3 --version
          echo "WORKSPACE=${WORKSPACE}"
        '''
      }
    }

    stage('Prepare Env') {
      steps {
        script {
          sh 'cp -f ai-code-player.env.example .env.deploy'
          echo "Started from ai-code-player.env.example"

          def loadedSecret = false
          def tried = []
          def credIds = []
          def paramId = (params.ENV_CREDENTIAL_ID ?: 'ai-code-player-env-file').toString().trim()
          credIds.add(paramId)
          ['ai-code-player-env-file', 'ai-code-player-env-file.env', 'ai-coder-env-file'].each { extra ->
            if (!credIds.contains(extra)) {
              credIds.add(extra)
            }
          }

          for (int i = 0; i < credIds.size(); i++) {
            def credId = credIds.get(i).toString()
            tried.add(credId)
            if (loadedSecret) {
              break
            }
            try {
              withCredentials([file(credentialsId: credId, variable: 'ENV_FILE')]) {
                sh '''
                  echo "Secret file path bound: $ENV_FILE"
                  test -f "$ENV_FILE" || { echo "ERROR: credential file path missing"; exit 1; }
                  cp -f "$ENV_FILE" .env.deploy
                  echo "Copied Secret file → .env.deploy"
                '''
              }
              loadedSecret = true
              echo "Loaded Secret file credential ID: ${credId}"
            } catch (err) {
              echo "No Secret file with ID '${credId}' (${err})"
            }
          }

          if (!loadedSecret) {
            def candidates = [
              '/var/jenkins_home/secrets/ai-code-player.env',
              '/var/jenkins_home/ai-code-player.env',
              'ai-code-player.env',
            ]
            for (int k = 0; k < candidates.size(); k++) {
              def p = candidates.get(k)
              if (fileExists(p)) {
                sh "cp -f '${p}' .env.deploy"
                loadedSecret = true
                echo "Using env file: ${p} → .env.deploy"
                break
              }
            }
          }

          if (!loadedSecret) {
            echo "WARN: no Jenkins Secret file loaded. Using ai-code-player.env.example (Gemini/TTS keys will be empty until you upload the secret file)."
          }

          sh '''
            set -e
            python3 scripts/normalize_deploy_env.py .env.deploy --public-app-url "${PUBLIC_APP_URL:-}"
            echo "=== Key check (values hidden) ==="
            if grep -qE '^GEMINI_API_KEY=.+' .env.deploy && ! grep -qE '^GEMINI_API_KEY=(PASTE_|CHANGE_ME|$)' .env.deploy; then
              echo "GEMINI_API_KEY=SET"
            else
              echo "GEMINI_API_KEY=MISSING"
              echo "ERROR: upload Jenkins Secret file ID ai-code-player-env-file with GEMINI_API_KEY=..."
              exit 1
            fi
            if grep -qE '^GOOGLE_TTS_API_KEY=.+' .env.deploy && ! grep -qE '^GOOGLE_TTS_API_KEY=(PASTE_|CHANGE_ME|$)' .env.deploy; then
              echo "GOOGLE_TTS_API_KEY=SET"
            else
              echo "GOOGLE_TTS_API_KEY=MISSING (Chirp voice will fail until you add it)"
            fi
          '''
          echo "Prepared .env.deploy for ${params.DEPLOY_ENV}"
        }
      }
    }

    stage('Clean') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set +e
          echo "=== Stop previous AI Coding Tutor containers ==="
          docker compose -f docker-compose.yml down --remove-orphans || true
          docker rm -f aicoder-backend-1 aicoder-frontend-1 aicoder-postgres-1 aicoder-redis-1 aicoder-code-runner-1 aicoder-worker-1 2>/dev/null || true
          docker rmi -f ai-coder-api:latest ai-coder-web:latest ai-coder-runner:latest 2>/dev/null || true
        '''
      }
    }

    stage('Docker Build') {
      steps {
        sh '''
          set -e
          echo "Building API image..."
          docker build -t ${API_IMAGE} -t ${API_IMAGE_LATEST} ./backend

          echo "Building code-runner image..."
          docker build -t ${RUNNER_IMAGE} -t ${RUNNER_IMAGE_LATEST} ./services/code-runner

          echo "Building Web image..."
          docker build \
            --build-arg "API_ORIGIN=http://backend:8000" \
            -t ${WEB_IMAGE} -t ${WEB_IMAGE_LATEST} \
            ./frontend

          docker images | grep ai-coder | head -n 20 || docker images | head -n 12
        '''
      }
    }

    stage('Smoke Test') {
      steps {
        sh '''
          set -e
          docker run --rm \
            -e DATABASE_URL=sqlite:///./jenkins_smoke.db \
            -e TTS_PROVIDER=browser \
            -e TTS_FALLBACK_PROVIDER=browser \
            -e GEMINI_API_KEY= \
            ${API_IMAGE} \
            python /app/scripts/jenkins_smoke.py
        '''
      }
    }

    stage('Deploy') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set -e
          cp -f .env.deploy .env
          set +x
          set -a
          # shellcheck disable=SC1091
          . ./.env
          set +a
          set -x

          export API_HOST_PORT="${API_HOST_PORT:-8010}"
          export WEB_HOST_PORT="${WEB_HOST_PORT:-3010}"
          export RUNNER_HOST_PORT="${RUNNER_HOST_PORT:-8090}"
          export POSTGRES_HOST_PORT="${POSTGRES_HOST_PORT:-5433}"
          export REDIS_HOST_PORT="${REDIS_HOST_PORT:-6380}"

          echo "Publishing UI ${WEB_HOST_PORT} API ${API_HOST_PORT}"
          docker compose -f docker-compose.yml down --remove-orphans || true

          echo "Starting Postgres + Redis + sandbox..."
          docker compose -f docker-compose.yml up -d --build postgres redis code-runner

          echo "Waiting for Postgres..."
          i=1
          while [ "$i" -le 30 ]; do
            if docker compose -f docker-compose.yml exec -T postgres pg_isready -U tutor -d aicoder >/dev/null 2>&1; then
              echo "Postgres ready"
              break
            fi
            echo "attempt ${i}: postgres starting"
            i=$((i + 1))
            sleep 2
          done

          echo "Starting API, worker, frontend (no Kokoro — Google Cloud TTS)..."
          docker compose -f docker-compose.yml up -d --build backend worker frontend

          echo "Waiting for API health..."
          i=1
          while [ "$i" -le 45 ]; do
            if docker compose -f docker-compose.yml exec -T backend curl -fsS http://127.0.0.1:8000/api/v1/health >/tmp/aicoder_health.json 2>/dev/null; then
              echo "API healthy"
              cat /tmp/aicoder_health.json
              echo
              docker compose -f docker-compose.yml ps
              exit 0
            fi
            echo "attempt ${i}: api starting"
            i=$((i + 1))
            sleep 3
          done
          echo "API health check failed"
          docker compose -f docker-compose.yml ps || true
          docker compose -f docker-compose.yml logs --tail=120
          exit 1
        '''
      }
    }

    stage('Post-Deploy Check') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set -e
          echo "=== Container status ==="
          docker compose -f docker-compose.yml ps || true
          echo "=== API health ==="
          docker compose -f docker-compose.yml exec -T backend curl -fsS http://127.0.0.1:8000/api/v1/health
          echo
          echo "=== Web responds ==="
          docker compose -f docker-compose.yml exec -T frontend wget -qO- http://127.0.0.1:3000 >/tmp/aicoder_web.html 2>/dev/null || true
          if [ -s /tmp/aicoder_web.html ]; then
            echo "web_ok bytes=$(wc -c </tmp/aicoder_web.html)"
          else
            echo "WARN: could not fetch web HTML from inside container"
            docker compose -f docker-compose.yml logs frontend --tail=40 || true
          fi
        '''
      }
    }

    stage('Host Nginx') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        sh '''
          set -e
          echo "=== Install host nginx from git (doc-vault style) ==="
          export PUBLIC_APP_URL="${PUBLIC_APP_URL:-https://play.doxstation.com}"
          export PUBLIC_HOST="${PUBLIC_APP_URL}"
          bash scripts/install_host_nginx.sh || echo "WARN: could not update /etc/nginx/sites-available/aicoder from git"
        '''
      }
    }
  }

  post {
    success {
      echo "AI Coding Tutor ${params.DEPLOY_ENV} build #${env.BUILD_NUMBER} succeeded"
      echo "UI: ${params.PUBLIC_APP_URL}"
      echo "API: host port ${env.API_HOST_PORT} /api/v1/health"
      echo "HTTPS: ${params.PUBLIC_APP_URL} (host nginx from deploy/host-nginx-aicoder.conf)"
    }
    failure {
      echo "AI Coding Tutor build #${env.BUILD_NUMBER} failed — check stage logs"
      sh 'docker compose -f docker-compose.yml logs --tail=120 || true'
    }
    always {
      sh 'rm -f .env.deploy.bak || true'
    }
  }
}
