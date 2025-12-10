# SpringBoot自动装配

Spring Boot自动配置主要是@EnableAutoConfiguration实现的，@EnableAutoConfiguration注解导入AutoConfigurationImportSelector类,通过selectImports方法调用SpringFactoriesLoader.loadFactoryNames()扫描所有含有META-INF/spring.factories文件的jar包，将spring.factories文件中@EnableAutoConfiguration对应的类注入到IOC容器中


## 注解链路
```
@SpringBootApplication
=>
@EnableAutoConfiguration
=>
@EnableAutoConfiguration
=>
@Import(AutoConfigurationImportSelector.class)
=>
getAutoConfigurationEntry:122, AutoConfigurationImportSelector (org.springframework.boot.autoconfigure)
```

## 代码链路
```
getAutoConfigurationEntry:122, AutoConfigurationImportSelector (org.springframework.boot.autoconfigure)
process:434, AutoConfigurationImportSelector$AutoConfigurationGroup (org.springframework.boot.autoconfigure)
getImports:879, ConfigurationClassParser$DeferredImportSelectorGrouping (org.springframework.context.annotation)
processGroupImports:809, ConfigurationClassParser$DeferredImportSelectorGroupingHandler (org.springframework.context.annotation)
process:780, ConfigurationClassParser$DeferredImportSelectorHandler (org.springframework.context.annotation)
parse:193, ConfigurationClassParser (org.springframework.context.annotation)
processConfigBeanDefinitions:320, ConfigurationClassPostProcessor (org.springframework.context.annotation)
postProcessBeanDefinitionRegistry:237, ConfigurationClassPostProcessor (org.springframework.context.annotation)
invokeBeanDefinitionRegistryPostProcessors:280, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:96, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:707, AbstractApplicationContext (org.springframework.context.support)
refresh:533, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refresh:747, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
main:35, StartApplication (com.zuzuche.widget.start)
```
## 自动装配流程图

![spring_boot_autoconfigure](spring_boot_autoconfigure.png)