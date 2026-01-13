# Repo Analysis: Solana-Prediction-Market

Role: `Architect`
URL: https://github.com/HyperBuildX/Solana-Prediction-Market.git

## ML and Data Signals
- Signals: None detected
- Notebooks: False
- Data dir: False

## Integration Signals (top files)
- prediction-market-backend\src\config.ts (score 3)
- prediction-market-frontend\src\data\data.ts (score 3)
- Readme.md (score 2)
- prediction-market-backend\readme.md (score 2)
- prediction-market-smartcontract\README.md (score 2)
- prediction-market-backend\src\index.ts (score 2)
- prediction-market-backend\src\oracle_service\simulateFeed.ts (score 2)
- prediction-market-backend\src\prediction_market_sdk\config.ts (score 2)
- prediction-market-backend\src\prediction_market_sdk\index.ts (score 2)
- prediction-market-frontend\src\types\type.ts (score 2)
- prediction-market-frontend\src\utils\index.ts (score 2)
- prediction-market-frontend\src\components\oracle_service\simulateFeed.ts (score 2)
- prediction-market-frontend\src\components\prediction_market_sdk\index.ts (score 2)
- prediction-market-smartcontract\tests\prediction.ts (score 2)

## Prompt and Persona Definitions (hits)
- `prediction-market-backend\src\prediction_market_sdk\index.ts`
  - Excerpt: `latestBlockHash = await provider.connection.getLatestBlockhash(\n      provider.connection.commitment\n    );\n\n    const lutMsg1 = new TransactionMessage({\n      payerKey: auth.publicKey,\n      recentBlockhash: latestBlockHash.blockhash,\n      instructions: [transferIx]\n    }).compileToV0Message();\n\n    const lutVTx1 = new VersionedTransaction(lutMsg1);\n    lutVTx1.sign([auth.payer]);\n  \n    const lutId1 = await provider.connection.sendTransaction(lutVTx1);\n    console.log("send sol tx:", lutId`
- `prediction-market-backend\src\prediction_market_sdk\idl\idl.ts`
  - Excerpt: `export type Prediction = {\n  "version": "0.1.0",\n  "name": "prediction",\n  "instructions": [\n    {\n      "name": "initialize",\n      "accounts": [\n        {\n          "name": "payer",\n          "isMut": true,\n          "isSigner": true\n        },\n        {\n          "name": "global",\n          "isMut": true,\n          "isSig`
- `prediction-market-backend\src\prediction_market_sdk\idl\prediction.json`
  - Excerpt: `{\n  "version": "0.1.0",\n  "name": "prediction",\n  "instructions": [\n    {\n      "name": "initialize",\n      "accounts": [\n        {\n          "name": "payer",\n          "isMut": true,\n          "isSigner": true\n        },\n        {\n          "name": "global",\n          "isMut": true,\n          "isSig`
- `prediction-market-frontend\src\components\oracle_service\simulateFeed.ts`
  - Excerpt: `r.connection.getLatestBlockhash(\n        queue.program.provider.connection.commitment\n    );\n\n    const messageV0 = new TransactionMessage({\n        payerKey: param.wallet.publicKey,\n        recentBlockhash: latestBlockHash.blockhash,\n        instructions: [initIx],\n    }).compileToV0Message();\n    \n    const vtx = new VersionedTransaction(messageV0);\n    const sim = await queue.program.provider.connection.simulateTransaction(vtx);\n    console.log("custom feed simulation:", sim);\n\n    vtx.sign`
- `prediction-market-frontend\src\components\prediction_market_sdk\index.ts`
  - Excerpt: `Blockhash(\n    solConnection.commitment\n  );\n\n  const creatTx = new Transaction({\n    feePayer: param.wallet.publicKey,\n    ...latestBlockHash,\n  });\n  creatTx.add(initTx).add(mintTx);\n  \n  const addressesMain: PublicKey[] = [];\n  creatTx.instructions.forEach((ixn) => {\n    ixn.keys.forEach((key) => {\n      addressesMain.push(key.pubkey);\n    });\n  });\n  \n  const messageV0 = new TransactionMessage({\n    payerKey: param.wallet.publicKey,\n    recentBlockhash: latestBlockHash.blockhash,`
- `prediction-market-frontend\src\components\prediction_market_sdk\idl\idl.ts`
  - Excerpt: `export type Prediction = {\n  "version": "0.1.0",\n  "name": "prediction",\n  "instructions": [\n    {\n      "name": "initialize",\n      "accounts": [\n        {\n          "name": "payer",\n          "isMut": true,\n          "isSigner": true\n        },\n        {\n          "name": "global",\n          "isMut": true,\n          "isSig`
- `prediction-market-frontend\src\components\prediction_market_sdk\idl\prediction.json`
  - Excerpt: `{\n  "version": "0.1.0",\n  "name": "prediction",\n  "instructions": [\n    {\n      "name": "initialize",\n      "accounts": [\n        {\n          "name": "payer",\n          "isMut": true,\n          "isSigner": true\n        },\n        {\n          "name": "global",\n          "isMut": true,\n          "isSig`

Unk = Uncle
Target: 35+ users
