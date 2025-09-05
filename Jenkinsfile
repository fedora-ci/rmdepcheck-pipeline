#!groovy

retry (10) {
    // load pipeline configuration into the environment
    httpRequest("${FEDORA_CI_PIPELINES_CONFIG_URL}/environment").content.split('\n').each { l ->
        l = l.trim(); if (l && !l.startsWith('#')) { env["${l.split('=')[0].trim()}"] = "${l.split('=')[1].trim()}" }
    }
}

def pipelineMetadata = [
    pipelineName: 'rmdepcheck',
    pipelineDescription: 'Run rmdepcheck test.',
    testCategory: 'functional',
    testType: 'installability',
    maintainer: 'Fedora CI',
    docs: 'https://codeberg.org/AdamWill/rmdepcheck',
    contact: [
        irc: '#fedora-ci',
        email: 'ci@lists.fedoraproject.org'
    ],
]
def bodhiId
def artifactIds
def testingFarmRequestId
def testingFarmResult
def config
def ignoreList
def pipelineRepoUrlAndRef
def hook
def runUrl


pipeline {

    agent none

    libraries {
        lib("fedora-pipeline-library@${env.PIPELINE_LIBRARY_VERSION}")
    }

    options {
        buildDiscarder(logRotator(daysToKeepStr: env.DEFAULT_DAYS_TO_KEEP_LOGS, artifactNumToKeepStr: env.DEFAULT_ARTIFACTS_TO_KEEP))
        timeout(time: env.DEFAULT_PIPELINE_TIMEOUT_MINUTES, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    parameters {
        string(name: 'BODHI_UPDATE_ID', defaultValue: '', trim: true, description: '"Bodhi updated ID; Example: FEDORA-2025-7826f19244')
        string(name: 'ARTIFACT_IDS', defaultValue: '', trim: true, description: 'A comma-separated list of all koji builds in the update; Example: koji-build:46436038')
        string(name: 'TEST_PROFILE', defaultValue: env.FEDORA_CI_RAWHIDE_RELEASE_ID, trim: true, description: "A name of the test profile to use; Example: ${env.FEDORA_CI_RAWHIDE_RELEASE_ID}")
    }

    environment {
        TESTING_FARM_API_KEY = credentials('testing-farm-api-key')
    }

    stages {
        stage('Prepare') {
            agent {
                label pipelineMetadata.pipelineName
            }
            steps {
                script {
                    bodhiId = params.BODHI_UPDATE_ID
                    artifactIds = params.ARTIFACT_IDS

                    checkout scm
                    config = loadConfig(profile: params.TEST_PROFILE)
                    pipelineRepoUrlAndRef = [url: "${getGitUrl()}", ref: "${getGitRef()}"]

                    if (!bodhiId) {
                        abort('BODHI_UPDATE_ID is missing')
                    }
                    if (!artifactIds) {
                        abort('ARTIFACT_IDS is missing')
                    }
                }
                artifactIds.split(',').each { artifactId ->
                    sendMessage(type: 'queued', artifactId: artifactId, pipelineMetadata: pipelineMetadata, dryRun: isPullRequest())
                }
            }
        }

        stage('Schedule Test') {
            agent {
                label pipelineMetadata.pipelineName
            }
            steps {
                script {
                    def requestPayload = [
                        api_key: "${env.TESTING_FARM_API_KEY}",
                        test: [
                            tmt: pipelineRepoUrlAndRef
                        ],
                        environments: [
                            [
                                arch: "x86_64",
                                os: [ compose: "${config.compose}" ],
                                variables: [
                                    BODHI_UPDATE_ID: bodhiId
                                ]
                            ]
                        ]
                    ]
                    hook = registerWebhook()
                    requestPayload['notification'] = ['webhook': [url: hook.getURL()]]
                    requestPayload['environments'][0]['tmt'] = [
                        context: config.tmt_context[getTargetArtifactType(artifactId)]
                    ]

                    def response = submitTestingFarmRequest(payloadMap: requestPayload)
                    testingFarmRequestId = response['id']
                }
                artifactIds.split(',').each { artifactId ->
                    sendMessage(type: 'running', artifactId: artifactId, pipelineMetadata: pipelineMetadata, dryRun: isPullRequest())
                }
            }
        }

        stage('Wait for Test Results') {
            agent none
            steps {
                script {
                    def response = waitForTestingFarm(requestId: testingFarmRequestId, hook: hook)
                    testingFarmResult = response.apiResponse
                    runUrl = "${FEDORA_CI_TESTING_FARM_ARTIFACTS_URL}/${testingFarmRequestId}"
                }
            }
        }
    }

    post {
        always {
            evaluateTestingFarmResults(testingFarmResult)
        }
        success {
            artifactIds.split(',').each { artifactId ->
                sendMessage(type: 'complete', artifactId: artifactId, pipelineMetadata: pipelineMetadata, runUrl: runUrl, dryRun: isPullRequest())
            }
        }
        failure {
            artifactIds.split(',').each { artifactId ->
                sendMessage(type: 'error', artifactId: artifactId, pipelineMetadata: pipelineMetadata, runUrl: runUrl, dryRun: isPullRequest())
            }
        }
        unstable {
            artifactIds.split(',').each { artifactId ->
                sendMessage(type: 'complete', artifactId: artifactId, pipelineMetadata: pipelineMetadata, runUrl: runUrl, dryRun: isPullRequest())
            }
        }
        aborted {
            script {
                if (isTimeoutAborted(timeout: env.DEFAULT_PIPELINE_TIMEOUT_MINUTES, unit: 'MINUTES')) {
                    artifactIds.split(',').each { artifactId ->
                        sendMessage(type: 'error', artifactId: artifactId, errorReason: 'Timeout has been exceeded, pipeline aborted.', pipelineMetadata: pipelineMetadata, runUrl: runUrl, dryRun: isPullRequest())
                    }
                }
            }
        }
    }
}
