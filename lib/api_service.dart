// -- lib/api_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl;
  final http.Client client;
  String? csrfToken;
  String? sessionCookie;

  ApiService({required this.baseUrl, http.Client? httpClient}) : client = httpClient ?? http.Client();

  Future<void> fetchCsrfToken() async {
    try {
      final response = await client.get(Uri.parse('$baseUrl/walt2'));
      if (response.statusCode == 200) {
        final cookies = response.headers['set-cookie'];
        if (cookies != null) {
          final csrfMatch = RegExp(r'csrf_token=([^;]+)').firstMatch(cookies);
          final sessionMatch = RegExp(r'session=([^;]+)').firstMatch(cookies);
          csrfToken = csrfMatch?.group(1);
          sessionCookie = sessionMatch?.group(1);
        }
      }
    } catch (e) {
      print("Error fetching CSRF token: $e");
      throw Exception('Failed to fetch CSRF token'); // Propagate the error
    }
  }

  Future<String> getNewBioInitialMessage() async {
    try {
      final response = await client.get(
        Uri.parse('$baseUrl/api/walt2/new_bio'),
        headers: {"Content-Type": "application/json"},
      );

      if (response.statusCode != 200) {
        throw Exception("Server error: ${response.statusCode}");
      }

      if (response.body.isEmpty) {
        throw Exception("Empty response from server");
      }

      final data = jsonDecode(response.body);
      if (data['error'] != null) {
        throw Exception("Server error: ${data['error']}");
      }
      return data['initial_message'] ?? "No response provided";
    } catch (e) {
      print("Error in getNewBioInitialMessage: $e");
      throw Exception('Failed to get initial message: $e'); // Re-throw the exception
    }
  }


  Future<String> analyzePrompt(String prompt) async {
    try {
      final response = await client.post(
        Uri.parse('$baseUrl/api/walt2/analyze'),
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken ?? "",
          "Cookie": "session=$sessionCookie",
          "Referer": "$baseUrl/walt2/",
        },
        body: "user_query=${Uri.encodeComponent(prompt)}",
      );

      if (response.statusCode != 200) {
        throw Exception("Server error: ${response.statusCode}");
      }

      if (response.body.isEmpty) {
        throw Exception("Empty response from server");
      }
      final responseData = jsonDecode(response.body);
       if (responseData['error'] != null) {
        throw Exception("Server error: ${responseData['error']}");
      }
      return responseData['response'] ?? "No response provided";
    } catch (e) {
      print("Error in analyzePrompt: $e");
      throw Exception('Failed to analyze prompt: $e'); // Re-throw the exception
    }
  }

  Future<String> continueBio(String checkpointData) async { // New continueBio function
    try {
      final response = await client.post(
        Uri.parse('$baseUrl/api/walt2/continue_bio'), // Use continue_bio API endpoint
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken ?? "",
          "Cookie": "session=$sessionCookie",
          "Referer": "$baseUrl/walt2/",
        },
        body: "checkpoint_data=${Uri.encodeComponent(checkpointData)}", // Send checkpoint_data in body
      );

      if (response.statusCode != 200) {
        throw Exception("Server error in continueBio: ${response.statusCode} - ${response.body.substring(0, 200)}...");
      }

      if (response.body.isEmpty) {
        throw Exception("Empty response from server in continueBio");
      }
      final responseData = jsonDecode(response.body);
       if (responseData['error'] != null) {
        throw Exception("Server error in continueBio: ${responseData['error']}");
      }
      return responseData['initial_message'] ?? "No response provided"; // Extract initial_message
    } catch (e) {
      print("Error in continueBio: $e");
      throw Exception('Failed to continue bio: $e'); // Re-throw the exception
    }
  }


  void closeClient() {
    client.close();
  }
}
// -- lib/api_service.dart
