/*global fetch*/
/*global btoa*/

import {
    LexRuntimeV2Client,
    RecognizeTextCommand,
  } from "@aws-sdk/client-lex-runtime-v2";
  
  const lexRuntimeClient = new LexRuntimeV2Client({ region: process.env.REGION });
  
  export const handler = async (event) => {
    console.log({ event });
  
    const lex_request = {
      botAliasId: process.env.LEX_ALIAS_ID, // Use your alias ID
      botId: process.env.LEX_BOT_ID, // Use your bot ID
      localeId: "en_US",
      sessionId: "randomSession",
      text: event["query"], // Text query from Lex
    };
  
    let tags = [];
  
    try {
      // Call Lex to process the text
      const command = new RecognizeTextCommand(lex_request);
      const lexResponse = await lexRuntimeClient.send(command);
  
      console.log("Lex Response:", JSON.stringify(lexResponse));
  
      // Extract slots from Lex response
      const slots = lexResponse["sessionState"]["intent"]["slots"];
  
      tags = Object.keys(slots).map((k) => {
        return {
          term: {
            labels: slots[k]["value"]["interpretedValue"],
          },
        };
      });
  
      console.log("Extracted tags for search:", tags);
    } catch (error) {
      console.error("Error calling Lex bot:", error);
    }
  
    // Query OpenSearch with the extracted tags
    try {
      const os_response = await fetch(
        `${process.env.OS_ENDPOINT}/photo-tags/_search`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Basic ${btoa(
              `${process.env.OPENSEARCH_USERNAME}:${process.env.OPENSEARCH_PASSWORD}`
            )}`,
          },
          body: JSON.stringify({
            query: {
              bool: {
                should: tags,
                minimum_should_match: 1,
              },
            },
          }),
        }
      );
  
      console.log("Returned response from OpenSearch");
  
      const os_data = await os_response.json();
  
      const images = os_data.hits.hits.map((hit) => {
        return {
          imageSrc: `https://${hit._source.bucket}.s3.${process.env.REGION}.amazonaws.com/${hit._source.objectKey}`,
          tags: hit._source.labels,
        };
      });
  
      return {
        statusCode: 200,
        body: JSON.stringify(images), // Return images found in OpenSearch
      };
    } catch (error) {
      console.error("Error querying OpenSearch:", error);
      const fallbackImages = [
        {
          imageSrc:
            "https://cloudfour.com/examples/img-currentsrc/images/kitten-large.png",
          tags: ["random"],
        },
      ];
      return {
        statusCode: 200,
        body: JSON.stringify(fallbackImages),
      };
    }
  };
  