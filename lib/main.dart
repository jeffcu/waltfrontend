// -- lib/main.dart
import 'package:flutter/material.dart';
import 'walt2_splash_screen.dart';
import 'api_service.dart'; // Import ApiService

void main() {
  runApp(const Walt2App());
}

class Walt2App extends StatefulWidget { // Make Walt2App StatefulWidget to manage ApiService lifecycle
  const Walt2App({super.key});

  @override
  Walt2AppState createState() => Walt2AppState();
}

class Walt2AppState extends State<Walt2App> {
  late final ApiService apiService; // ApiService instance at app level

  @override
  void initState() {
    super.initState();
    apiService = ApiService(baseUrl: "https://virtual-lab-staging-jeff-b43cbb10d55f.herokuapp.com"); // Initialize ApiService here
  }

  @override
  void dispose() {
    apiService.closeClient(); // Dispose ApiService when the entire app is disposed
    super.dispose();
  }


  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Walt2 Biographer',
      theme: ThemeData(
        primaryColor: const Color(0xFF007AFF),
        scaffoldBackgroundColor: const Color(0xFFF7F7F7),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: Color(0xFF333333)),
        ),
      ),
      home: Walt2SplashScreen(apiService: apiService), // Pass ApiService to SplashScreen
    );
  }
}
// -- lib/main.dart
